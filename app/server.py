from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO

from fastai.vision import *

export_file_url = 'https://www.googleapis.com/drive/v3/files/1-6ACEO2XCVWtHDM84fCAmspkx99zpKbA?alt=media&key=AIzaSyCZRHQRQoWYvCCzyax5lxAdrNyfP-nibSo'
export_file_name = 'New_P100.pkl'
classes =  ['dipstation', 'Battle', 'BenchPress', 'InclineBenchPress', 'HammerStrengthmachine', 'LatPullDownMachine', 'PecDeckMachine', 'PullupBar', 'DumbBells', 'tricepbars', 'PreacherBench', 'HandgripExerciser', 'reversehyper', 'Plyometric', 'airresistance', 'Stair', 'Ankle', 'LegCurlMachine', 'LegPressMachine', 'LegExtensionMachine', 'HackSquatMachine', 'CalfMachines', 'LegAbductionAbductionMachine', 'prowler', 'Mini', 'Inversion', 'Vibration', 'PowerRack', 'MaxiClimber', 'StretchingMachine', 'SmithMachine', 'Suspension', 'CablesandPulleys', 'KettleBells', 'Roman', 'AbdominalBench', 'AbCoaster', 'Stationary', 'CruiserBikes', 'FixieBikes', 'MountainBike', 'RecumbentBikes', 'RoadBikes', 'SpinBikes', 'Comfort', 'Treadmill', 'Mini_Exercise_\ufeffBikes', 'metalplates', 'Medicine', 'Pedometers', 'Pull', 'BloodGlucoseMeter', 'GPSWatches', 'GymnasticsGrips&Gloves', 'hoverboard', 'JumpRope', 'ResistanceBand', 'YogaMat', 'Fitness', 'barbells', 'WallBall', 'FoamRoller', 'Stabilityball', 'AgilityLadder', 'BalanceBoards', 'BalanceBoards']
path = Path(__file__).parent


app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(model_file_url, path/'models'/f'{model_file_name}.pth')
    data_bunch = load_learner(path, classes,
        ds_tfms=get_transforms(), size=224).normalize(imagenet_stats)
    learn = create_cnn(data_bunch, models.resnet34, pretrained=False)
    learn.load(model_file_name)
    return learn

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    img_bytes = await (data['file'].read())
    img = open_image(BytesIO(img_bytes))
    return JSONResponse({'result': learn.predict(img)[0]})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app, host='0.0.0.0', port=8080)
