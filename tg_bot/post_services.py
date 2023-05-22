from dff.script import Context
import requests


def response_refiner(ctx: Context):
    last_request = ctx.last_request.text
    last_response = ctx.last_response.text
    if last_response is None:
        # nothing to refine
        return
    response = requests.post(url='http://response_refinement:8030/refine', json={'question': last_request, 'response': last_response, })
    model_response = response.json()
    ctx.set_last_response(model_response['refined_resp'])
