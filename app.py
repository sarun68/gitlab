from flask import Flask, render_template, request, url_for
from bjt_model import calculate_bjt_dc

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form_data = {}

    if request.method == "POST":
        try:
            vcc = float(request.form.get("vcc", 0))
            r1 = float(request.form.get("r1", 0))
            r2 = float(request.form.get("r2", 0))
            rc = float(request.form.get("rc", 0))
            re = float(request.form.get("re", 0))
            beta = float(request.form.get("beta", 0))
            vbe = float(request.form.get("vbe", 0))

            result = calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe)
        except ValueError as e:
            error = str(e)
        except Exception as e:
            error = f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}"

    return render_template("index.html", result=result, error=error, form=form_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
