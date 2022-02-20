<h1>Exceed Project Backend</h1>
    A <b>very</b> simple api made with FastAPI and MongoDB.
<h2>Requirements</h2>
    To avoid any compatibility issues, it is recommended to run this API on <b>Python 3.9.x</b>.
    <table>
        <tr>
            <td><b>Module</b></td>
            <td><b>Version</b></td>
        </tr>
        <tr>
            <td>FastAPI</td>
            <td>0.73.0</td>
        </tr>
        <tr>
            <td>PyMongo</td>
            <td>4.0.1</td>
        </tr>
        <tr>
            <td>Uvicorn</td>
            <td>0.17.1</td>
        </tr>
    </table>

Simply use the following command to install all dependencies:
<pre>
pip install -r requirements.txt
</pre>
<h2>Running the API with Uvicorn</h2>
Run the following command to start the server:
<pre>
uvicorn main:app
</pre>
