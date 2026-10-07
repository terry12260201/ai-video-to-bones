import asyncio,json,sys,datetime,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
HERE=Path(__file__).parent
async def main():
    code=Path(sys.argv[1]).read_text()
    # 路徑代號：這包放在 <工作資料夾>/工具腳本/ 底下時自動對到，不用改每支腳本。
    #   __SHAKE_WORK__    ＝工作資料夾（預設＝本檔的上一層），可用環境變數 SHAKE_WORK 覆蓋
    #   __SHAKE_PROJECT__ ＝專案根目錄（放 beagle.glb 與 Ai videos/，預設＝工作資料夾的上一層），可用 SHAKE_PROJECT 覆蓋
    work=Path(os.environ.get('SHAKE_WORK') or HERE.parent).resolve()
    proj=Path(os.environ.get('SHAKE_PROJECT') or work.parent).resolve()
    code=code.replace('__SHAKE_WORK__',str(work)).replace('__SHAKE_PROJECT__',str(proj))
    server=StdioServerParameters(command=sys.executable,args=[str(HERE/'mcp_bridge.py')])
    async with stdio_client(server) as (r,w):
        async with ClientSession(r,w) as session:
            init=await session.initialize()
            res=await session.call_tool('execute_blender_code',{'code':code})
            record={'time':datetime.datetime.now().isoformat(),'script':sys.argv[1],'server':init.serverInfo.model_dump(),'tool':'execute_blender_code','code':code,'response':res.model_dump(mode='json')}
            with (HERE.parent/'驗證'/'MCP操作紀錄.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
            for c in res.content:
                if c.type=='text':print(c.text)
            if res.isError:raise RuntimeError('MCP tool returned error')
asyncio.run(main())
