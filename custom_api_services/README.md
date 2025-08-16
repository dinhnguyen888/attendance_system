# FastAPI with OpenCV

## Setup Instructions

1. **Create a Virtual Environment**:

    ```bash
    python -m venv venv
    ```

2. **Activate the Virtual Environment**:

    - On Windows:
        ```bash
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the FastAPI Application**:

    ```bash
    uvicorn main:app --reload
    ```

5. **Access the Application**:

    - Open your browser and navigate to `http://127.0.0.1:8000` to see the welcome message.
    - Visit `http://127.0.0.1:8000/opencv-version` to check the OpenCV version.

6. **Deactivate the Virtual Environment**:
    ```bash
    deactivate
    ```

By using a virtual environment, you can isolate your development environment and avoid conflicts with system-wide Python packages.
