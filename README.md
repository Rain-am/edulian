# 领星报关自动化

本项目用于从领星 API 拉取 FBA 发货计划和本地产品资料，生成报关 Excel，并支持将发货计划明细写入 MySQL。

## 目录结构

```text
src/
  common/      # 领星鉴权客户端、通用 Excel 能力
  shipment/    # 发货计划：拉取、拼接报关明细、导出 Excel、写入 MySQL
  product/     # 物料表：产品列表/详情拉取、20 条预览导出
tests/         # 单元测试
docs/          # 领星接口截图和字段依据
scripts/       # Linux 部署、检查、定时任务脚本
```

## 本地初始化

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

然后在 `.env` 中填写领星 API、MySQL 和可选 SSH 隧道配置。真实密钥、数据库密码、SSH 密码只放 `.env`，不要提交到 GitHub。

## 常用命令

检查领星鉴权：

```powershell
.\.venv\Scripts\python.exe main.py --check-auth
```

查看当前公网 IP，便于配置领星白名单：

```powershell
.\.venv\Scripts\python.exe main.py --show-ip --ip-repeat 3
```

生成发货计划报关 Excel：

```powershell
.\.venv\Scripts\python.exe main.py --job shipment --shipment-time 2026-06-13 --output output\real-2026-06-13.xlsx --debug-api
```

生成发货计划报关 Excel 并写入 MySQL：

```powershell
.\.venv\Scripts\python.exe main.py --job shipment --shipment-time 2026-06-13 --output output\real-2026-06-13.xlsx --write-db --debug-api
```

生成物料表 20 条预览：

```powershell
.\.venv\Scripts\python.exe main.py --job product-preview --limit 20 --output output\product-preview-20.xlsx --debug-api
```

## 发货计划输出

发货计划主表按 `发货单号 + SKU + 箱号` 生成稳定主键 `id`。主要字段包括确定出运月份、发货单号、采购主体、供应商、供应商地址、成交方式、付款方式名称、币别、SKU、份数、品名、中英文报关品名、单位、发货数量、采购价格、物流信息、箱号、箱数、重量、尺寸、体积和更新时间。

箱号来自“查询 FBA 发货单详情”的 `data.items[].box_no`，多个箱号会用英文逗号分隔。

## 物料表预览

物料表预览从产品列表接口获取 SKU 和更新时间，再调用产品详情接口补充品名、中文材质、单位、中文报关品名和海关编码。目前只导出 Excel 预览，不写入数据库。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall -q main.py src tests
```

## 云服务器部署

生成干净部署目录：

```powershell
.\scripts\make_deploy.ps1
```

上传 `deploy_package` 到 Linux 云服务器后执行：

```bash
bash scripts/setup_linux.sh
nano .env
bash scripts/check.sh
.venv/bin/python main.py --check-auth
bash scripts/run_once.sh
```

确认手动运行成功后安装每 20 分钟执行一次的定时任务：

```bash
bash scripts/install_cron.sh
crontab -l
tail -f logs/cron.log
```
