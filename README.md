# sing-box 1.12 规则集自动构建

此项目每天 04:17（Asia/Shanghai）自动更新规则集；它固定使用 **sing-box 1.12.12**，不会下载最新版本。

`GravityRyu` 的全部公开 Gist 会通过 GitHub 公共 API 分页读取。每个可转换文件保留原文件名，仅将最后一个扩展名改为 `.srs`，例如 `gistfile1.txt` 会生成 `gistfile1.srs`。

支持 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD`、`DOMAIN-REGEX`、`IP-CIDR`、`IP-CIDR6`。无法在 sing-box 规则集中表示的条目会在日志中提示并跳过。两个源文件生成同名目标时，构建会失败以避免覆盖。
