import os,json,datetime
import numpy as np
from fastapi import FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(title="OmniOnco AI API")

from pydantic import BaseModel

class PlanRequest(BaseModel):
    goal: str
    cancer_type: str

@app.post("/plan")
def plan_workflow(req: PlanRequest):
    goal_lower = req.goal.lower()
    plan = []
    
    if "mutat" in goal_lower: plan.append("mut")
    if "express" in goal_lower or "rna" in goal_lower or "transcript" in goal_lower: plan.append("exp")
    
    if "integrat" in goal_lower or ("mutat" in goal_lower and "express" in goal_lower): 
        if "mut" not in plan: plan.append("mut")
        if "exp" not in plan: plan.append("exp")
        plan.append("int")
        
    if "pathway" in goal_lower: plan.append("path")
    
    if "survival" in goal_lower or "clinical" in goal_lower or "biomarker" in goal_lower: 
        plan.append("bio")
        
    # Default fallback if nothing matches
    if not plan:
        plan = ["mut", "exp", "int", "path", "bio"]
        
    plan.append("llm")
    
    # De-duplicate while preserving order
    final_plan = []
    for p in ["mut", "exp", "int", "path", "bio", "llm"]:
        if p in plan:
            final_plan.append(p)
            
    return {"plan": final_plan}
class ChatRequest(BaseModel):
    message: str
    cancer_type: str
    context_genes: list = []

@app.post("/chat")
def chat(req: ChatRequest):
    import openai
    client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    sys = "You are an AI Multi-Omics Agent, a bioinformatics assistant. Keep answers brief and scientific."
    prompt = f"Context Genes: {req.context_genes}\nCancer: {req.cancer_type}\nUser: {req.message}"
    
    try:
        response = client.chat.completions.create(
            model="llama3.2:3b",
            messages=[{"role":"system","content":sys}, {"role":"user","content":prompt}],
            temperature=0.3,
            max_tokens=200
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Agent Error: {str(e)}"}

app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
_mc,_ec,_ic,_cc,_rc,_pc,_bc={},{},{},{},{},{},{}
VALID={"BRCA","SKCM"}
def _chk(c):
    if c not in VALID: raise HTTPException(400,"Invalid cancer type")

class NE(json.JSONEncoder):
    def default(self,o):
        if isinstance(o,np.integer): return int(o)
        if isinstance(o,np.floating): return float(o)
        if isinstance(o,np.ndarray): return o.tolist()
        return super().default(o)
def _j(d): return json.loads(json.dumps(d,cls=NE))
@app.get("/health")
def health(): return {"status":"ok","ts":datetime.datetime.now().isoformat()}
@app.get("/mutation/{cancer_type}")
def mutation(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _mc:
        from pipeline.mutation import MutationAnalyzer
        from config import DATA_PATHS
        _mc[cancer_type]=_j(MutationAnalyzer(DATA_PATHS[cancer_type]["mutations"]).summarize())
    return _mc[cancer_type]
@app.get("/expression/{cancer_type}")
def expression(cancer_type:str,top_n:int=500):
    _chk(cancer_type)
    k=f"{cancer_type}_{top_n}"
    if k not in _ec:
        from pipeline.expression import ExpressionAnalyzer
        from config import DATA_PATHS
        a=ExpressionAnalyzer(DATA_PATHS[cancer_type]["expression"])
        df=a.run_differential_expression(top_n=top_n)
        _ec[k]=_j(a.summarize(df))
    return _ec[k]
@app.get("/integration/{cancer_type}")
def integration(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _ic:
        from pipeline.integrator import MultiOmicsIntegrator
        i=MultiOmicsIntegrator(mutation(cancer_type),expression(cancer_type, 500))
        _ic[cancer_type]=_j(i.generate_report())
    return _ic[cancer_type]
@app.get("/clinical/{cancer_type}")
def clinical(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _cc:
        from pipeline.clinical import ClinicalAnalyzer
        from config import DATA_PATHS
        _cc[cancer_type]=_j(ClinicalAnalyzer(DATA_PATHS[cancer_type]["clinical"]).summarise())
    return _cc[cancer_type]
@app.get("/ranking/{cancer_type}")
def ranking(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _rc:
        from pipeline.ranker import CandidateRanker
        _rc[cancer_type]=_j(CandidateRanker(mutation(cancer_type),expression(cancer_type, 500)).rank())
    return _rc[cancer_type]
@app.get("/pathway/{cancer_type}")
def pathway(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _pc:
        from pipeline.pathway import PathwayAnalyzer
        integ=integration(cancer_type)
        conv=integ.get("convergent_genes",{})
        genes=list(set(conv.get("mutated_AND_upregulated",[]))|set(conv.get("mutated_AND_downregulated",[])))
        if not genes:
            exp=expression(cancer_type, 500)
            genes=(exp.get("top_upregulated",[])+exp.get("top_downregulated",[]))[:20]
        _pc[cancer_type]=_j(PathwayAnalyzer(genes).run())
    return _pc[cancer_type]
@app.get("/biomarker/{cancer_type}")
def biomarker(cancer_type:str):
    _chk(cancer_type)
    if cancer_type not in _bc:
        import pandas as pd
        from pipeline.expression import ExpressionAnalyzer
        from pipeline.biomarker import BiomarkerExplorer
        from config import DATA_PATHS
        a=ExpressionAnalyzer(DATA_PATHS[cancer_type]["expression"])
        clin=pd.read_csv(DATA_PATHS[cancer_type]["clinical"],sep="\t",comment="#",low_memory=False)
        _bc[cancer_type]=_j(BiomarkerExplorer(a.expr_log,clin).run())
    return _bc[cancer_type]
@app.get("/full/{cancer_type}")
def full(cancer_type:str, goal:str=None):
    _chk(cancer_type)
    res = {
        "cancer_type":cancer_type,"computed_at":datetime.datetime.now().isoformat(),
        "mutation":mutation(cancer_type),"expression":expression(cancer_type, 500),
        "integration":integration(cancer_type),"clinical":clinical(cancer_type),
        "ranking":ranking(cancer_type),
        "pathway":pathway(cancer_type),
        "biomarker":biomarker(cancer_type)
    }
    
    # If the user has a custom goal, dynamically generate the hypothesis!
    if goal and goal.strip() and goal != "Identify key oncogenic driver genes":
        try:
            import copy
            from openai import OpenAI
            client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
            
            conv = res["integration"].get("convergent_genes", {})
            mut_up = conv.get("mutated_AND_upregulated", [])
            mut_only = conv.get("mutated_only", [])[:10]
            deg_only = conv.get("deg_only", [])[:10]
            
            prompt = f"""
Goal: {goal}
Cancer Type: {cancer_type}
Convergent Targets (Mutated & Upregulated): {mut_up}
Top Mutation-Only: {mut_only}
Top Expression-Only: {deg_only}

Provide a concise 2-3 sentence biological interpretation (hypothesis) of these specific gene lists in the context of the user's goal. Be highly scientific and specific.
"""
            resp = client.chat.completions.create(
                model='llama3.2:3b',
                messages=[
                    {"role": "system", "content": "You are OmniOnco AI, an expert computational biologist analyzing multi-omics data."}, 
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            custom_hypothesis = resp.choices[0].message.content.strip()
            
            # Deep copy so we don't overwrite the cached default integration
            res["integration"] = copy.deepcopy(res["integration"])
            res["integration"]["hypothesis"] = custom_hypothesis
        except Exception as e:
            print(f"[LLM Error] {e}")
            
    return res
if __name__=="__main__":
    import uvicorn, socket
    # Auto-select port: try 8001 first, fall back to 8002
    port = 8001
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", 8001)) == 0:
            port = 8002
            print(f"[WARNING] Port 8001 is in use, using port {port} instead.")
    print("=" * 50)
    print(f"  OmniOnco AI API  ->  http://localhost:{port}")
    print(f"  Swagger Docs     ->  http://localhost:{port}/docs")
    print("=" * 50)
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
