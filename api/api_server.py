import sys
import os
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.PFT_main import PFTSystem

app = FastAPI(
    title="PFT Automated Interpretation Tool",
    description="A web tool and API to provide preliminary interpretation of Pulmonary Function Tests.",
    version="1.1.0",
)

templates_path = os.path.join(os.path.dirname(__file__), '..', 'templates')
templates = Jinja2Templates(directory=templates_path)

pft_system = PFTSystem(log_level='INFO')


@app.get("/", response_class=HTMLResponse, summary="Main User Interface")
async def get_main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/interpret-form", response_class=HTMLResponse, summary="Handle Form Submission")
async def handle_interpret_form(
    request: Request,
    age: int = Form(...),
    sex: str = Form(...),
    height_cm: float = Form(...),
    weight_kg: float = Form(...),
    pre_fvc_liters: float = Form(...),
    pre_fvc_pp: int = Form(...),
    pre_fev1_liters: float = Form(...),
    pre_fev1_pp: int = Form(...),
    pre_ratio: int = Form(...),
    post_fvc_liters: float = Form(...),
    post_fvc_pp: int = Form(...),
    post_fev1_liters: float = Form(...),
    post_fev1_pp: int = Form(...),
    post_ratio: int = Form(...),
):
    try:
        pft_data_dict = {
            "demographics": {
                "age": age, "sex": sex, "height_cm": height_cm, "weight_kg": weight_kg
            },
            "pft_results": {
                "pre_bronchodilator": {
                    "fvc": {"liters": pre_fvc_liters, "percent_predicted": pre_fvc_pp},
                    "fev1": {"liters": pre_fev1_liters, "percent_predicted": pre_fev1_pp},
                    "fev1_fvc_ratio": {"value": pre_ratio}
                },
                "post_bronchodilator": {
                    "fvc": {"liters": post_fvc_liters, "percent_predicted": post_fvc_pp},
                    "fev1": {"liters": post_fev1_liters, "percent_predicted": post_fev1_pp},
                    "fev1_fvc_ratio": {"value": post_ratio}
                }
            }
        }
        result = pft_system.process_single_pft(pft_data_dict, output_format='json')

        if result['status'] == 'error':
            return templates.TemplateResponse("results_partial.html", {
                "request": request,
                "error": result['error']
            })
        
        return templates.TemplateResponse("results_partial.html", {
            "request": request, 
            "report": result['report']
        })

    except Exception as e:
        return templates.TemplateResponse("results_partial.html", {
            "request": request, 
            "error": f"An unexpected server error occurred: {str(e)}"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8080, reload=True)