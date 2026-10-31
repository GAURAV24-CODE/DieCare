from flask import Flask, render_template, request, redirect, url_for, session
import os
import pickle

app = Flask(__name__)

# Use an environment variable for the secret key in deployment
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "diacare-development-key"
)

# Load the trained model and scaler
with open("Model/standardScalar.pkl", "rb") as file:
    scaler = pickle.load(file)

with open("Model/modelForPrediction.pkl", "rb") as file:
    model = pickle.load(file)


@app.route("/")
def index():
    return render_template("index.html")


# PAGE 1: Patient details
@app.route("/screening", methods=["POST"])
def screening():
    session["patient"] = {
        "full_name": request.form.get("full_name", "").strip(),
        "mobile": request.form.get("mobile", "").strip(),
        "age": request.form.get("age", "").strip(),
        "gender": request.form.get("gender", "").strip(),
        "city": request.form.get("city", "").strip()
    }

    return redirect(url_for("screening_form"))


# PAGE 2: Screening form
@app.route("/screening-form")
def screening_form():
    if "patient" not in session:
        return redirect(url_for("index"))

    return render_template(
        "home.html",
        patient=session["patient"]
    )


# PAGE 3: Process prediction
@app.route("/predict", methods=["POST"])
def predict():
    if "patient" not in session:
        return redirect(url_for("index"))

    try:
        patient = session["patient"]

        # Get screening inputs
        pregnancies = int(request.form.get("Pregnancies"))
        glucose = float(request.form.get("Glucose"))
        blood_pressure = float(request.form.get("BloodPressure"))
        skin_thickness = float(request.form.get("SkinThickness"))
        insulin = float(request.form.get("Insulin"))
        bmi = float(request.form.get("BMI"))
        pedigree = float(request.form.get("DiabetesPedigreeFunction"))

        # Use the age entered on Page 1
        age = float(patient["age"])

        # Prepare input in the same order used during model training
        input_data = [[
            pregnancies,
            glucose,
            blood_pressure,
            skin_thickness,
            insulin,
            bmi,
            pedigree,
            age
        ]]

        # Scale input and predict
        scaled_data = scaler.transform(input_data)
        prediction = model.predict(scaled_data)[0]

        if prediction == 1:
            result = "Higher Risk"
            result_message = (
                "The model identified a higher likelihood of diabetes. "
                "This is not a diagnosis. Please consult a qualified "
                "healthcare professional for appropriate testing."
            )
        else:
            result = "Lower Risk"
            result_message = (
                "The model identified a lower likelihood of diabetes "
                "based on the entered values. This does not rule out "
                "diabetes. Consult a healthcare professional if you "
                "have symptoms or concerns."
            )

        # Store details temporarily for the report
        session["measurements"] = {
            "Pregnancies": pregnancies,
            "Glucose": glucose,
            "BloodPressure": blood_pressure,
            "SkinThickness": skin_thickness,
            "Insulin": insulin,
            "BMI": bmi,
            "DiabetesPedigreeFunction": pedigree,
            "Age": age
        }

        session["prediction"] = result

        return render_template(
            "single_prediction.html",
            patient=patient,
            measurements=session["measurements"],
            result=result,
            result_message=result_message
        )

    except (ValueError, TypeError):
        return "Please enter valid numeric values in all screening fields.", 400


# Display result again if the patient refreshes the page
@app.route("/result")
def result():
    if "patient" not in session or "prediction" not in session:
        return redirect(url_for("index"))

    result = session["prediction"]

    if result == "Higher Risk":
        result_message = (
            "The model identified a higher likelihood of diabetes. "
            "This is not a diagnosis. Please consult a healthcare "
            "professional for appropriate testing."
        )
    else:
        result_message = (
            "The model identified a lower likelihood of diabetes "
            "based on the entered values. This does not rule out "
            "diabetes. Consult a healthcare professional if you "
            "have symptoms or concerns."
        )

    return render_template(
        "single_prediction.html",
        patient=session["patient"],
        measurements=session["measurements"],
        result=result,
        result_message=result_message
    )


if __name__ == "__main__":
    app.run(debug=True)