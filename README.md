# 移动爱家（原和家亲）Home Assistant 集成

~~本项目正在开发阶段~~ 暂停更新 [#23](https://github.com/XiaoMiku01/hass-hjq/issues/23) , 如果遇到 Bug 请通过 [issue](https://github.com/XiaoMiku01/hass_hjq/issues) 反馈, [这里](https://github.com/XiaoMiku01/hass_hjq/issues/3) 统计一下`可用`/`不可用`的设备  
本人手中的设备有限, 欢迎其他开发者贡献代码  

## 支持设备

-   [x] 手机号密码登录
-   [x] 网络摄像头接入
-   [ ] 智能插座开关接入
-   [ ] 其他设备接入（待定）
-   [ ] 摄像头事件上报

## 使用方法

1. 使用你选择的工具打开 Home Assistant 配置的目录（你可以在该目录中找到 `configuration.yaml` 文件）。
2. 如果该目录中没有 `custom_components` 文件夹，则需要创建一个。
3. 在 `custom_components` 文件夹中，创建一个名为 `hass_hjq` 的新文件夹。
4. 从该仓库的 `custom_components/hass_hjq/` 目录中下载所有文件。
5. 将下载的文件放入你刚创建的 `hass_hjq` 文件夹中。
6. 重启 Home Assistant。
7. 在 Home Assistant 的 UI 中，进入 “设置” -> “集成”，点击 “+” 并搜索 “移动爱家（原和家亲）”。

## 相关问题

1. 和家亲的监控只有网络流, 没有发现 rstp/onvif 本地流
2. 暂时无法接入 Homekit, 原因可能是网络流只有 h265 编码, 但是 homekit 需要 h264 的视频流 (待解决)  


## 免责声明（Disclaimer）

本项目的代码及相关文档是出于开源社区贡献的目的开发和发布，旨在为 [Home Assistant](https://github.com/home-assistant) 提供兼容性支持和功能扩展。作者不对任何个人或组织使用本代码所造成的任何直接或间接后果承担责任。该代码及其衍生产品仅限于合法用途，用户需自行确保其在使用本项目时遵守相关法律法规，包括但不限于知识产权和逆向工程相关的法律条款。

本项目代码基于 [Apache License 2.0](./LICENSE) 许可证发布，用户可以根据该许可证的条款自由使用、修改和分发本项目代码，但需保留原始的版权声明。

**免责声明要点**：

1. 本代码和项目仅出于学习、研究和开源社区贡献的目的，作者不保证代码的准确性、完整性和可用性。
2. 用户需自行承担使用本代码的法律责任，并自行确保其在使用该代码时未侵犯任何第三方的权利。
3. 本代码未与任何官方产品或服务相关联，亦不代表任何第三方利益。
4. 作者不对任何因使用本项目代码而导致的损害、数据丢失或其他任何损失承担责任。
5. **如果您认为本项目中的任何部分侵犯了您的合法权益，请立即通过 <xiao@m1ku.de> 与作者联系，作者将在确认后尽快删除相关内容。**

使用本代码即表示您同意以上免责声明内容。
