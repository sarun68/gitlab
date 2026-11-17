from flask import Flask, render_template, request
from bjt_model import calculate_bjt_dc

app = Flask(__name__)


def _form_float(name: str, default: float = 0.0) -> float:
    raw = request.form.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return float(raw)


def _form_optional_float(name: str):
    raw = request.form.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    return float(raw)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form_data = {}

    if request.method == "POST":
        try:
            mode = request.form.get("mode", "divider")
            vcc = _form_float("vcc")
            r1 = _form_float("r1")
            r2 = _form_float("r2")
            rc = _form_float("rc")
            re = _form_float("re")
            beta = _form_float("beta")
            vbe = _form_float("vbe")
            rb = _form_optional_float("rb")

            result = calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe,
                                      mode=mode, rb=rb)
            form_data = request.form.to_dict()
        except ValueError as e:
            error = str(e)
            form_data = request.form.to_dict()
        except Exception as e:
            error = f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}"
            form_data = request.form.to_dict()

    return render_template("index.html", result=result, error=error, form=form_data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
