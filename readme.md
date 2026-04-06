# 智能停车场管理系统

这是一个基于 Flask 实现的简易智能停车场管理系统。系统通过模拟停车场的车辆进出、车位预约、费用计算等功能，提供了一个直观的停车场运营管理界面。

## 功能特性

*   **实时车位状态监控**: 以网格形式动态展示停车场内每个车位的实时状态（可用、占用、预约）。
*   **车位预约**: 用户可以为普通车辆或特殊车辆（如需特殊停放的车辆）预约车位，预约有15分钟的保留时间。
*   **自动入场/离场**: 系统模拟车辆的自动入-场和离场流程。入场时为车辆自动分配最近的可用车位，离场时自动结算费用。
*   **智能计费**:
    *   停车首30分钟免费。
    *   超过30分钟后，按每小时5元的标准计费（不足一小时按一小时计算）。
    *   特殊车辆免费停放。
*   **寻车功能**: 输入车牌号即可快速定位车辆所停放的车位。
*   **停车记录查询**: 查看所有车辆的历史停车记录，包括入场时间、离场时间、停车时长和费用。
*   **运营数据统计**: 以图表形式展示停车场的总收入、总停车次数以及每日的收入和车流量。

## 技术栈

*   **后端**: Python, Flask
*   **数据库**: SQLite
*   **前端**: HTML, CSS, JavaScript (jQuery, Chart.js)

## 快速开始

1.  **环境准备**:
    确保您已安装 Python 3。

2.  **克隆项目**:
    ```bash
    git clone <your-repository-url>
    cd <project-directory>
    ```

3.  **创建并激活虚拟环境**:
    *   **Windows**:
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **macOS/Linux**:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

4.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **运行应用**:
    ```bash
    python app.py
    ```
    应用启动后，数据库 `parking.db` 和初始数据会自动创建。

6.  **访问应用**:
    在浏览器中打开 `http://127.0.0.1:5000` 即可访问系统主页。

## API 接口

系统提供了一系列 RESTful API 来与前端进行交互：

*   `POST /reserve`: 预约一个车位。
*   `POST /enter`: 车辆入场。
*   `POST /exit`: 车辆离场并结算。
*   `POST /find_car`: 根据车牌号查找车辆位置。
*   `GET /spot`: 获取所有车位的实时状态。
*   `GET /api/records`: 获取所有停车记录。
*   `GET /api/stats`: 获取运营统计数据。

## 页面截图

*   **主页/车位监控**:
    ![主页截图](https://example.com/screenshot-main.png)

*   **停车记录**:
    ![记录截图](https://example.com/screenshot-records.png)

*   **数据统计**:
    ![统计截图](https://example.com/screenshot-stats.png)

*(请将上面的图片链接替换为实际的截图链接)*
