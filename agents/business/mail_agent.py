import re  #regular expression library for parsing scores
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import (
    WRITER_TOOLS, REVIEWER_TOOLS,
    init_email_db, save_email_to_db
)

WRITER_PROMPT = """You are an Expert Email Copywriter with 10+ years of experience.

Your job:
- Write engaging, professional emails that convert
- Match tone to email type (welcome, sales, newsletter, etc.)
- Subject line: under 50 chars, curiosity-driven
- Body: under 200 words, scannable, with clear CTA
- Use personalization placeholders like {name}, {product}
- Include ONE clear Call-to-Action (CTA) in brackets like [Get Started ->]
- Sound human, not robotic

Process:
1. First, use get_email_templates tool to find similar past templates
2. Use check_grammar tool to verify your draft
3. Output ONLY the email in this format:

SUBJECT: [subject line here]

[body here]

If revising based on feedback:
- Address each feedback point specifically
- Don't completely rewrite - improve the weak areas
- Keep what's working
"""

REVIEWER_PROMPT = """You are a Strict Email Editor at a top marketing agency.

Your job: Critically evaluate emails and score them.

Score on 4 dimensions (each 1-10):
1. TONE: Appropriate for email type? Sounds human, not robotic?
2. PERSUASION: Compelling? Will the reader take action?
3. CTA: Clear, specific, actionable? Only ONE CTA?
4. GRAMMAR: No errors? Subject under 50 chars? Body under 200 words?

Process:
1. Use check_spam_score tool to assess spam risk
2. Use check_grammar tool for style issues
3. Output in EXACTLY this format:

SCORES:
Tone: X/10
Persuasion: X/10
CTA: X/10
Grammar: X/10

SPAM_CHECK: [result from tool]
GRAMMAR_CHECK: [result from tool]

FEEDBACK:
[If ANY score <7: specific, actionable feedback for the writer]
[If ALL scores >=7: "APPROVED - no changes needed"]

Be brutally honest. Better to catch issues now than after sending.
"""


class EcommerceAgent(BaseAgent):
    NAME = "EmailCraft"
    DESCRIPTION = "Multi-agent email writer + reviewer - Writer drafts, Reviewer scores, revisions until all scores >=7"
    ICON = "email"
    DOMAIN = "Business"
    
    def __init__(self):
        init_email_db()
        
        self.llm = get_llm(temperature=0.5)
        self.reviewer_llm = get_llm(temperature=0.1)
        
        
        self.writer_agent = create_agent(
            model=self.llm,
            tools=WRITER_TOOLS,
            checkpointer=InMemorySaver(),
        )
        
        self.reviewer_agent = create_agent(
            model=self.reviewer_llm,
            tools=REVIEWER_TOOLS,
            checkpointer=InMemorySaver(),
        )
    
    def run(self, user_input: str, thread_id: str = "default", 
            max_revisions: int = 3, **kwargs) -> dict:
        email_type = kwargs.get("email_type", "General")
        full_brief = f"Email type: {email_type}\nBrief: {user_input}"
        
        history = []
        
        # Step 1: Writer creates initial draft
        writer_config = {"configurable": {"thread_id": f"writer-{thread_id}"}} 
        writer_result = self.writer_agent.invoke(
            {"messages": [
                {"role": "system", "content": WRITER_PROMPT},
                {"role": "user", "content": full_brief}
            ]},
            writer_config
        )
        draft = self._extract_content(writer_result)
        
        history.append({
            "version": 1, "draft": draft, "scores": None, "feedback": None
        })
        
        # Step 2: Review + Revise loop
        for revision_num in range(1, max_revisions + 1):
            reviewer_config = {"configurable": {"thread_id": f"reviewer-{thread_id}-v{revision_num}"}} #draft ko review krne k liye thread id
            reviewer_result = self.reviewer_agent.invoke(
                {"messages": [
                    {"role": "system", "content": REVIEWER_PROMPT},
                    {"role": "user", "content": f"Review this email:\n\n{draft}\n\nEmail type: {email_type}"} #draft ko review krne k liye reviewer agent ko bhej rha h
                ]},
                reviewer_config
            )
            review = self._extract_content(reviewer_result)
            
            scores = self._parse_scores(review)
            history[-1]["scores"] = scores
            history[-1]["feedback"] = review
            
            if all(s >= 7 for s in scores.values()):
                save_email_to_db(user_input, email_type, draft, scores, 
                               revision_num - 1, "approved")
                return {
                    "final_email": draft, "scores": scores,
                    "revisions": revision_num - 1, "history": history,
                    "status": "approved"
                }
            # If not scores not 7+, prepare for next revision
            revision_input = (
                f"Revise this email based on reviewer feedback.\n\n"
                f"ORIGINAL BRIEF: {full_brief}\n\n"
                f"CURRENT DRAFT:\n{draft}\n\n"
                f"REVIEWER FEEDBACK:\n{review}\n\n"
                f"Address each feedback point. Keep what's working, fix what's weak."
            )
            
            writer_config = {"configurable": {"thread_id": f"writer-{thread_id}-rev{revision_num}"}}
            writer_result = self.writer_agent.invoke(
                {"messages": [
                    {"role": "system", "content": WRITER_PROMPT},
                    {"role": "user", "content": revision_input}
                ]},
                writer_config
            )
            draft = self._extract_content(writer_result)
            
            history.append({
                "version": revision_num + 1, "draft": draft, 
                "scores": None, "feedback": None
            })
        # If max revisions reached without approval, save in db and return
        final_scores = scores if 'scores' in locals() else {"tone": 5, "persuasion": 5, "cta": 5, "grammar": 5}
        save_email_to_db(user_input, email_type, draft, final_scores, 
                        max_revisions, "max_revisions_reached")
        
        return {
            "final_email": draft, "scores": final_scores,
            "revisions": max_revisions, "history": history,
            "status": "max_revisions_reached"
        }
    #helper methods data ko clean and readable format me convert krne k liye
    def _extract_content(self, result: dict) -> str:
        final_msg = result["messages"][-1]
        if isinstance(final_msg.content, list):
            return final_msg.content[0].get("text", "")
        return final_msg.content
    
    def _parse_scores(self, review_text: str) -> dict: #return clean dict help of regex
        scores = {"tone": 5, "persuasion": 5, "cta": 5, "grammar": 5}
        patterns = {
            "tone": r"tone.*?(\d+)\s*/\s*10",
            "persuasion": r"persuasion.*?(\d+)\s*/\s*10",
            "cta": r"cta.*?(\d+)\s*/\s*10",
            "grammar": r"grammar.*?(\d+)\s*/\s*10",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                scores[key] = int(match.group(1)) 
        return scores
    
    def render_ui(self):
        from .ui import render_ecommerce_ui
        render_ecommerce_ui(self)