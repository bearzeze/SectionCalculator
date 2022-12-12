import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, usd
import datetime as dt
import math
import smtplib
import socket

IEX_API_KEY = "export API_KEY=pk_e7260e58ccd74cb092488737c7102848"

# Configure application
app = Flask(__name__, template_folder="template")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///beamCalc.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    # Always 
    try:
        data = db.execute("SELECT * FROM users WHERE id = ?;", session["user_id"])
        session["credits"] = data[0]["credits"]
    except:
        return render_template("index.html")


    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("confirmation")

        data = db.execute("SELECT username FROM users;")

        # Blank username
        if not username:
            flash("Username cannot be blank!")
            return redirect("/register")

        # Username has less than 4 characters
        if len(username) < 4:
            flash("Username needs to have at least 4 characters!")
            return redirect("/register")

        # Check whether username is already in database
        if data:
            for person in data:
                if username == person["username"]:
                    flash("Username \"{0}\" is already taken!".format(username))
                    return redirect("/register")

        # Blank username
        if not password:
            flash("Password cannot be blank!")
            return redirect("/register")

        # Password has less than 4 characters
        if len(password) < 8:
            flash("Password needs to have at least 8 characters!")
            return redirect("/register")

        # Check if there is at least one digit in password
        for character in password:
            if character.isdigit():
                break
        else:
            flash("Password needs to have at least one digit (0-9)!")
            return redirect("/register")

        # Password is not confirmed
        if password != password_again:
            flash("Password is not confirmed!")
            return redirect("/register")

        # Inserting new user if
        hashed = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?);", username, hashed)
        flash("Enter your user data in order to login.")
        return render_template("login.html", error_occurs=False, username_exists=True, username=username)

    elif request.method == "GET":
        try:
            session["user_id"]
            return redirect("/")
        except:
            return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            flash("Username cannot be blank!")
            return redirect("/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?;", username)

        # Ensure username exists
        if len(rows) != 1:
            flash("Username doesn't exist!\nRegister instead.")
            return redirect("/register")

        # Ensure password was submitted
        if not password:
            flash("Password cannot be blank!")
            return render_template("login.html", username=username, username_exists=True, error_occurs=True)

        # Ensure password is correct
        if not check_password_hash(rows[0]["hash"], password):
            flash("Password is not correct! Try again.")
            return render_template("login.html", username=username, username_exists=True, error_occurs=True)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["credits"] = rows[0]["credits"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        try:
            session["user_id"]
            return redirect("/")
        except:
            return render_template("login.html", username_exists=False)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    return redirect("/")


@app.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    if request.method == "POST":
        old_pw_db = db.execute("SELECT * FROM users WHERE id = ?;", session["user_id"])[0]["hash"]

        old_pw_form = request.form.get("old_password")
        new_pw_form = request.form.get("new_password")
        new_pw_confirmation = request.form.get("confirmation")

        text1 = "We couldn't change your password!"
        text2 = "Password successfully changed!"

        # Any of input is blank
        if not old_pw_form or not new_pw_form or not new_pw_confirmation:
            flash("Password cannot be blank!")
            return render_template("change_password.html", title=text1, behavior="danger")

        # Checking typed current password and password from database
        if not check_password_hash(old_pw_db, old_pw_form):
            flash("You didn't type correct current password")
            return render_template("change_password.html", title=text1, behavior="danger")
        
        # Checking current password to not be the same as the new one
        if old_pw_form == new_pw_form:
            flash("Your new password is the same as the old one")
            return render_template("change_password.html", title=text1, behavior="danger")
        
        # New password has less than 8 characters
        if len(new_pw_form) < 8:
            flash("Password needs to have at least 8 characters!")
            return render_template("change_password.html", title=text1, behavior="danger")

        # Check if there is at least one digit in new password
        for character in new_pw_form:
            if character.isdigit():
                break
        else:
            flash("Password needs to have at least one digit (0-9)!")
            return render_template("change_password.html", title=text1, behavior="danger")

        # New password and confirmation password don't match
        if new_pw_form != new_pw_confirmation:
            flash("You didn't confirm new password with same password!")
            return render_template("change_password.html", title=text1, behavior="danger")
        

        # Update new password in the database
        new_hashed = generate_password_hash(password=new_pw_form, method="pbkdf2:sha256", salt_length=8)
        db.execute("UPDATE users SET hash = ? WHERE id = ?;", new_hashed, session["user_id"])
        
        flash("You have changed your password. Don't forget it!")
        return render_template("change_password.html", title=text2, behavior="success")

    elif request.method == "GET":
        return render_template("change_password.html", title="", behavior="")


@app.route("/credits", methods=["GET", "POST"])
@login_required
def credits():
    if request.method == "POST":
        current_credit = db.execute("SELECT * FROM users WHERE id = ?;", session["user_id"])[0]["credits"]

        add_credit = request.form.get("additional_credits")

        text1 = "We couldn't add credits to your account!"
        text2 = "Credits successfully added!"

        
        try:
            add_credit = int(add_credit)
            not_integer = False
        except:
            not_integer = True

        if not add_credit or not_integer or add_credit <= 0:
            flash("Value needs to be positive integer!")
            return render_template("credits.html", title=text1, behavior="danger")

        # Update new state of users credit
        new_credit = current_credit + add_credit
        db.execute("UPDATE users SET credits = ? WHERE id = ?;", new_credit, session["user_id"])

        word = "credits"
        if add_credit == 1:
            word = "credit"
            
        flash(f"You have added {add_credit} {word} to your account.")
        session["credits"] = new_credit

        return render_template("credits.html", title=text2, behavior="success")

    elif request.method == "GET":
        return render_template("credits.html", title="", behavior="")


@app.route("/calculate")
@login_required
def calculate():
    # Initializing calculate data in cache, which will be filled in methods
    # Visiting this page, also means that all previous data of caluclator is reseted
    session["calculator"] = {

        "loading_exists": {}, # It will be filled in loading_types() method
        "load_values": {},  # It will be filled in loading_values() method
        "allowed_stress": {}, # It will be filled in allowable_stresses() method
        "chosen_profile": {}, # It will be filled in choosing_profile() method
        "results": {},
        "optimization": {}
    }

    return render_template("calculate.html", current_credit=session["credits"])


@app.route("/loading_types", methods=["GET", "POST"])
@login_required
def loading_types():

    # 0 step should be done first - going to the calculate page 
    if not check_calculator_exists_and_credits():
        return redirect("/calculate")

    # This line of code (re)initialize statements about which loads exists in application
    session["calculator"]["loading_exists"] = {
        "axial": False, 
        "bending": False,
        "torsion": False,
        "counter": 0
    }


    if request.method == "POST":
        # Returns the value of checked checkboxes
        checkboxes = request.form.getlist('checkLoading')

        if checkboxes == []:
            return redirect("/loading_type")
        
        # In cache it will remember users choice for the type if he ever come back to this page
        for loading in checkboxes:
            session["calculator"]["loading_exists"][loading] = True
            session["calculator"]["loading_exists"]["counter"] += 1 

        # If everything went ok it goes to the 2nd step of typing values for loading 
        return redirect("/loading_values")

    elif request.method == "GET":
        return render_template("loading_types.html")


@app.route("/loading_values", methods=["GET", "POST"])
@login_required
def loading_values():

    # Checking first whether any past required data is missing
    # Then, 1 step should be done before entering loading values - choosing loading types
    if not check_calculator_exists_and_credits() or not check_loading_type_is_chosen():
        return redirect("/loading_types")

    # This line of code (re)initialize load values
    session["calculator"]["load_values"] = {
        "axial_force": 0,
        "bending_moment": 0,
        "torque": 0 }
    

    # Form
    if request.method == "POST":

        text_error = "Incorrect data entry"
        text_error_content = "The load values must be non-zero real numbers!"

        # If axial load is choosen in 1st step, input must be in correct format for axial force
        if session["calculator"]["loading_exists"]["axial"] == True:
            try:
                axial_force = float(request.form.get("axialForce"))
                if axial_force == 0:
                    raise 
                session["calculator"]["load_values"]["axial_force"] = abs(axial_force) * 1000
            except:
                flash(text_error_content)
                return render_template("loading_values.html", loading_type=session["calculator"]["loading_exists"], text_title=text_error)
        
        # If bending is choosen in 1st step, input must be in correct format for bending moment
        if session["calculator"]["loading_exists"]["bending"] == True:
            try:
                bending_moment = float(request.form.get("bendingMoment"))
                if bending_moment == 0:
                    raise 
                session["calculator"]["load_values"]["bending_moment"] = abs(bending_moment)
            except:
                flash(text_error_content)
                return render_template("loading_values.html", loading_type=session["calculator"]["loading_exists"], text_title=text_error)

        # If torsion is choosen in 1st step, input must be in correct format for torque
        if session["calculator"]["loading_exists"]["torsion"] == True:
            try:
                torque = float(request.form.get("torque"))
                if torque == 0:
                    raise 
                session["calculator"]["load_values"]["torque"] = abs(torque)
            except:
                flash(text_error_content)
                return render_template("loading_values.html", loading_type=session["calculator"]["loading_exists"], text_title=text_error)


        # If everything went ok it goes to the 3rd step of typing values for allowable stress(es)
        return redirect("/allowable_stress")

    
    elif request.method == "GET":
        return render_template("loading_values.html", loading_type=session["calculator"]["loading_exists"])


@app.route("/allowable_stress", methods=["GET", "POST"])
@login_required
def allowable_stress():

    # Checking first whether any past required data is missing
    # Then, 2nd step should be done before entering value for allowable stress that - entering loading values
    if not check_calculator_exists_and_credits() or not check_loading_type_is_chosen() or \
        not check_loading_values_entered():
        return redirect("/loading_values")

    # This line of code (re)initialize values important for determining allowable stress 
    session["calculator"]["allowed_stress"] = {
        "tensile_strength": 0,
        "safety_factor": 0,
        "allowable_stress": 0
    }

    if request.method == "POST":
        
        try:
            tensile_strength = float(request.form.get("tensileStrength"))
            safety_factor = float(request.form.get("safetyFactor"))

            if tensile_strength == 0 or safety_factor < 1:
                raise

            session["calculator"]["allowed_stress"]["tensile_strength"] = abs(tensile_strength)
            session["calculator"]["allowed_stress"]["safety_factor"] = abs(safety_factor)

            # Calculating allowable stress knowing tensile strength and safety factor
            session["calculator"]["allowed_stress"]["allowable_stress"] = abs(tensile_strength) / abs(safety_factor)
            
        except:
            flash("The stress and safety factor values must be non-zero real numbers!")
            return render_template("allowable_stress.html", text_title="Incorrect data entry")


        # If everything went ok it goes to the 4th step of choosing desired profile
        return redirect("/choosing_profile")


    elif request.method == "GET":
        return render_template("allowable_stress.html")


@app.route("/choosing_profile", methods=["GET", "POST"])
@login_required
def choosing_profile():

    # Checking first whether any past required data is missing
    # Then, 3rd step should be done before choosing profile that - calculate allowable stress 
    if not check_calculator_exists_and_credits() or not check_loading_type_is_chosen() or \
        not check_loading_values_entered() or not check_allowable_stress_value_entered():
        return redirect("/allowable_stress")
       
    # This line of code (re)initialize selected profile 
    session["calculator"]["chosen_profile"] = {
        "section": "",
        "profile": "",
        "available_sections": ["I_beam_section", "T_beam_section", "U_beam_section", "square_bar_section", "round_bar_section", "round_tube_section" , "square_tube_section", "rectangle_tube_section"]
    }

    # If user came with button Previous from the /result, it means that he wants to make new calculation so result in cache would be
    # cleared and reinitialized. Same applies to the optimization
    session["results"] = {}
    session["optimization"] = {}

    if request.method == "POST":
        # Returns the value of selected profile
        selected_option = str(request.form.get('profileSelection'))

        # This is default option in html
        if selected_option == "Choose Standard Cross Section":
            flash("You need to choose one of the possible cross section!")
            return render_template("choosing_profile.html", title="Invalid Cross Section Selection")
        
        
        session["calculator"]["chosen_profile"]["section"] = selected_option

        return redirect("/summary")

    elif request.method == "GET":
        return render_template("choosing_profile.html")


@app.route("/summary")
@login_required
def summary():

    # Checking first whether any past required data is missing
    # Then, 5th step should be checked - choosing profile, before going into summary
    if not check_calculator_exists_and_credits() or not check_loading_type_is_chosen() or \
       not check_loading_values_entered() or not check_allowable_stress_value_entered() or \
       not check_profile_is_chosen():
        return redirect("/choosing_profile")

    if request.method == "GET":
        return render_template("summary.html")
    

@app.route("/results")
@login_required
def results():
    # First function tries to reach cache
    # If user goes to the result page but with data from the calculation it means that results is already in cache
    # This will save users credit if he refreshes /results route.
    # Only if he goes to /calculate or reach again /choosing_profile route results will be cleared from the cache
    # and more credit will be decreased from the profile
    try:
        if session["results"]["profile_found"] == True:
            text_to_show_list = ["You will need" , f"{session['results']['min_required_profile']}", "cross-section in order to handle given load for given material."]
        else:
            data = session['results']['chosen_section'].split('_')
            
            text_to_show_list = ["No existing standard", f"{data[0]} {data[1]}", "section can handle given load for given material."]
        
        return render_template("results.html", profile_found=session['results']["profile_found"], text_to_show_list=text_to_show_list)
    
    # If there is no cache in session result, it means that calculation should be executed
    except:
        pass

    # If there is no data in cache about results, it needs to check everything first before calculation
    # Then, 5th step should be checked - choosing profile, before going into result
    # But summary page shouldn't be prerequisite for the printing results, only 5 steps above
    if not check_calculator_exists_and_credits() or not check_loading_type_is_chosen() or \
       not check_loading_values_entered() or not check_allowable_stress_value_entered() or \
       not check_profile_is_chosen():
        return redirect("/choosing_profile")

    # Table which will be checked in SQL
    table = session["calculator"]["chosen_profile"]["section"]
    
    # Result will be obtained from the function determine_profile()
    results = determine_profile(table)

    # Results are saved in cache
    session["results"] = results

    # Results
    if results["profile_found"] == True:
        session["calculator"]["chosen_profile"]["profile"] = results["min_required_profile"]
        text_to_show_list = ["You will need" , f"{results['min_required_profile']}", "cross-section in order to handle given load for given material."]
        # Credits will be decreased by one
        session["credits"] -= 1
        db.execute("UPDATE users SET credits = ? WHERE id = ?;",session["credits"], session["user_id"])
    else:
        session["calculator"]["chosen_profile"]["profile"] = None
        text_to_show_list = ["No existing standard", f"{results['chosen_section']}", "section can handle given load for given material."]


    return render_template("results.html", profile_found=results["profile_found"], text_to_show_list=text_to_show_list)
            
@app.route("/optimization")
@login_required
def optimization():
    # First function tries to reach cache
    # If optimization has been already done it will be saved in the cache session["optimization"]
    # This structure will try to get the results from cache if it is here than no new optimization had been done
    # This will prevent taking 3 credits from the user every time he goes to the /optimization route - for example refreshing it
    try:
        print(session["optimization"])
        if session["optimization"]["successful"] == True:
            text_to_show_list = ["Lightest possible cross-section is" , f"{session['optimization']['best_solution']}", "for your given load and given material."]
        else:
            text_to_show_list = "Not any available standard cross-section can handle given load for given material."
        
        return render_template("optimization.html", best_solution_found=session["optimization"]["successful"], text_to_show_list=text_to_show_list)

    # Except it means that optimization is called for the new data        
    except:
        pass

    # Checking first whether any past required data is missing
    # Then, 5th step should be checked - choosing profile, before going into result
    if not check_calculator_exists_and_credits or not check_loading_type_is_chosen() or \
       not check_loading_values_entered() or not check_allowable_stress_value_entered() or \
       not check_profile_is_chosen() or not check_results_exists():
        return redirect("/results")
    
    # If user has less than 3 credits, program will redirect toward /credits route
    if session["credits"] < 3:
        return redirect("/credits")


    session["optimization"] = {
        "successful": False,
        "best_solution": None,
    }

    # If torsion exists, only round cross section can be examined of
    if session["calculator"]["loading_exists"]["torsion"] == True:
        all_tables = ["round_bar_section", "round_tube_section"]
    else:
        all_tables = session["calculator"]["chosen_profile"]["available_sections"]


    opt_results = []
    # It will calculate results for every table in databse
    for table in all_tables:
        one_result = determine_profile(table)
        if one_result["profile_found"] == True:
            opt_results.append(one_result)
    
    # If there is any result algorithm will find best solution with minimum area
    if len(opt_results) >= 1:
        # Algorithm for finding solution with minimum area
        best_solution = opt_results[0]
        for solution in opt_results:
            if solution["area"] < best_solution["area"]:
                best_solution = solution
        
        session["optimization"]["successful"] = True
        session["optimization"]["best_solution"] = best_solution["min_required_profile"]
        text_to_show_list = ["Lightest possible cross-section is" , f"{session['optimization']['best_solution']}", "for your given load and given material."]
        # Credits will be decreased by three
        session["credits"] -= 3
        db.execute("UPDATE users SET credits = ? WHERE id = ?;",session["credits"], session["user_id"])
    else:
        session["optimization"]["successful"] = False
        text_to_show_list = "Not any available standard cross-section can handle given load for given material."


    return render_template("optimization.html", best_solution_found=session["optimization"]["successful"], text_to_show_list=text_to_show_list)


# Returns true if user has enough credits and he visited calculate page which is 0 step
def check_calculator_exists_and_credits():
    try:
        # Try to reach ["calculator"] dictionary, if user didn't visit calculate page it will raise exception
        session["calculator"]
        # If credits is less than 1 it will raise exception
        if session["credits"] <= 0:
            raise
        
        # If steps above are ok, this function will return True
        return True
    # Return false in order to redirects to loading_types page
    except:
        return False
    
# Returns true if user has chosen some loading type at 1 step
def check_loading_type_is_chosen():
    # If there is no data in chosen loading types, this means user never visited loading_type
    try:
        # Try to reach ["counter"] value if user didn't visit loading_type page it will raise exception
        session["calculator"]["loading_exists"]["counter"]
        # If there is data, but counter is 0 this means that user visited loading_types but didn't choose appropriate loading types
        if session["calculator"]["loading_exists"]["counter"] == 0:
            raise

        # If steps above are ok, this function will return True
        return True
    # Return false in order to redirects to loading_types page
    except:
        print("2. NE MOZE")
        return False

# Returns true if user has entered values for the loading types
def check_loading_values_entered():
    try:
        # Try to reach some ["load_values"] value if user didn't visit loading_values page it will raise exception
        session["calculator"]["load_values"]["axial_force"]
        # If every entry of loading values is 0 it cannot be accepted for further
        if session["calculator"]["load_values"]["axial_force"] == 0 \
            and session["calculator"]["load_values"]["bending_moment"] == 0 \
            and session["calculator"]["load_values"]["torque"] == 0:
            raise

        # If steps above are ok, this function will return True
        return True

    # Return false in order to redirects to load_values page
    except:
        return False

# Returns true if user has entered values for the allowable stress
def check_allowable_stress_value_entered():
    try:
        # If allowable stress is not set it will return false
        if session["calculator"]["allowed_stress"]["allowable_stress"] == 0:
            raise

        # If steps above are ok, this function will return True
        return True

    # Return false in order to redirects to allowable_stress page
    except:
        return False

# Returns true if user chosed profile
def check_profile_is_chosen():
    try:
        session["calculator"]["chosen_profile"]["section"]
        # If allowable stress is not set it redirects to that page
        if session["calculator"]["chosen_profile"]["section"] == "":
            raise

        # If steps above are ok, this function will return True
        return True

    # Redirects to allowable_stress page which will redirects further
    except:
        return False

# Returns true if calculation has been already done, so user wants to optimize section
# Because there is only one cross section for the elements where torsion is applied, it will return false also because 
# there is only full shaft cross section
def check_results_exists():
    try:
        session["results"]["profile_found"] 

        # If step above is ok, this function will return True
        return True

    except:
        return False

# Function which calcualte required area in mm^2 for the element loaded to axial stress
def calculate_required_area(F_axial, sigma_allowable):
    area = F_axial / sigma_allowable
    return area

# Function which calcualte required Wx (Wx = Ix/ymax) in mm^3 for the element loaded to bending stress
def calculate_required_Wx(M_bending, sigma_allowable):
    Wx = M_bending / sigma_allowable
    return Wx

# Function which calcualte required Wo (Wo = Io/rmax) in mm^3 for the element loaded to torsional
def calculate_required_diameter(M_bending, T_torque, sigma_allowable):
    # Diameter will be determined only by including bending and torque, later will be checked against axial stress also if it exists
    # Three theorem are used (1st and 2nd -> https://extrudesign.com/how-to-calculate-shaft-diameter-under-twisting-and-bending-moment/):

    # 1) Maximum shear stress theory (MSS) -> tau_allowable = 1/2 * sqrt(sigma_bending^2 + 4*tau^2) 
    tau_allowable = 0.6 * sigma_allowable
    diameter_MSS = (16 / tau_allowable / math.pi * (math.sqrt(M_bending**2 + T_torque**2)))**(1/3)

    # 2) Maximum normal stress theory (MNS) -> sigma_allowable = 1/2 * sigma_bending + 1/2 * sqrt(sigma_bending^2 + 4*tau^2)
    diameter_MNS = (32 / sigma_allowable / math.pi * 1/2 * (M_bending + (math.sqrt(M_bending**2 + T_torque**2))))**(1/3)

    # 3) Von misses
    diameter_VMS = (  math.sqrt((32 * M_bending / math.pi)**2 + 3 * (16 * T_torque / math.pi)**2) / sigma_allowable )**(1/3)

    # It returns maximum value from those two 
    print(diameter_MSS, diameter_MNS, diameter_VMS)
    diameter = max(diameter_MSS, diameter_MNS, diameter_VMS)  
    return diameter


def determine_profile(table, required_area=None, required_Wx=None, required_diameter=None):

    results = {
        # Chosen section can be "I_beam", "U_beam", "T_beam", "round_bar" , "round_tube", "square_bar" , "square_tube"  or"rectangle_tube"
        "chosen_section": table.split('_')[0] + "_" + table.split('_')[1],
        "min_required_profile": None,
        "profile_found": None,
        "area": None, 
    }

    # Internal load values
    axial_force = session["calculator"]["load_values"]["axial_force"] # N
    bending_moment = session["calculator"]["load_values"]["bending_moment"] * 1000 # Nmm
    torque = session["calculator"]["load_values"]["torque"] * 1000 # Nmm

    sigma_allowable =  session["calculator"]["allowed_stress"]["allowable_stress"]

    # AXIAL STRESS ONLY
    # results will be determined based on required_area
    # There will be no checkcking of stress
    if  axial_force != 0 and bending_moment == 0 and torque == 0:
        required_area = calculate_required_area(axial_force, sigma_allowable)
        all_possible_solutions = db.execute("SELECT * FROM ? WHERE area >= ? ORDER BY area ASC;", table, required_area)
    
    # NORMAL STRESS ONLY - bending exists, and possible axial force, but no torque
    elif bending_moment != 0 and torque == 0:
        required_Wx = calculate_required_Wx(bending_moment, sigma_allowable)
        all_possible_solutions = db.execute("SELECT * FROM ? WHERE Wx >= ? ORDER BY Wx ASC;", table, required_Wx)

    # TANGENTIAL STRESS EXISTS - torque exists and optionally bending and axial stress
    # Hypothesis will be applied where sigma_equivalent =  sqrt(sigma_normal^2 + 3 * tangential ^ 2)
    else:
        # Because only round shaft can be used, required diameter will be calculated
        # For tube also minimum diameter will be calculated and then searched throuh its table for the first solution that satisfie
        required_diameter = calculate_required_diameter(bending_moment, torque, sigma_allowable)
        
        # Now because this required diameter is when it is full not shallow, for tube it will be calculated
        # required Wx based on required diameter, and it will try with first Wx from the tube table with that required Wx
        # For the round profile Wo is always 2*Wx so searching by Wx is sufficient
        if results["chosen_section"] == "round_tube":
            required_Wx = required_diameter**3 * math.pi / 32
            all_possible_solutions = db.execute("SELECT * FROM ? WHERE Wx >= ? ORDER BY Wx ASC;", table,  required_Wx)
        # Else it is round bar and required diameter is sufficient
        else:
            all_possible_solutions = db.execute("SELECT * FROM ? WHERE diameter >= ? ORDER BY Wx ASC;", table,  required_diameter)
        

    # Only if there are at least one possible solution, checking stress will be applied  
    if len(all_possible_solutions) > 0:
        # This loop will be executed unless normal stress is less than allowable stress or
        # there is no more possible profiles in table
        # Current row in table is examined
        current_row = 0
        while True:
            F_a = axial_force
            M_s = bending_moment
            T_u = torque

            allowable_stress =  sigma_allowable

            # For different cross section, different way of calculating geometric characteristics
            # Only round section (full and shallow) can have Wo
            if results["chosen_section"] in ["round_bar", "round_tube"]:
                A = all_possible_solutions[current_row]["area"]
                Wx = all_possible_solutions[current_row]["Wx"]
                Wo = all_possible_solutions[current_row]["Wo"]

            else:
                A = all_possible_solutions[current_row]["area"]
                Wx = all_possible_solutions[current_row]["Wx"]
                Wo = 1


            # Von-Misses Stress formula is applied
            # IF there are no torsion, then this equivalent_normal_stress will become normal stress
            equivalent_normal_stress =  math.sqrt((F_a / A    +    M_s / Wx)**2 + 3 * (T_u  / Wo)**2)
            print(f"sigma_e = {round(equivalent_normal_stress, 2)} MPa <= {allowable_stress} ")

            if equivalent_normal_stress <= allowable_stress:
                results["profile_found"] = True

                if results["chosen_section"] in ["I_beam", "U_beam", "T_beam"]:
                    results["min_required_profile"] = all_possible_solutions[current_row]["symbol"]

                elif results["chosen_section"]  == "square_bar":
                    side = all_possible_solutions[current_row]["side"]
                    results["min_required_profile"] = f"\u25A2{side} mm"

                elif results["chosen_section"]  == "round_bar":
                    diameter = all_possible_solutions[current_row]["diameter"]
                    results["min_required_profile"] = f"\u00D8{diameter} mm"

                elif results["chosen_section"]  == "round_tube":
                    diameter = all_possible_solutions[current_row]["diameter"]
                    thickness = all_possible_solutions[current_row]["thickness"]
                    results["min_required_profile"] = f"\u00D8{diameter}/{thickness}wall mm"
                
                elif results["chosen_section"]  == "square_tube":
                    side = all_possible_solutions[current_row]["side"]
                    thickness = all_possible_solutions[current_row]["thickness"]
                    results["min_required_profile"] = f"\u25A2{side}/{thickness}wall mm"

                elif results["chosen_section"]  == "rectangle_tube":
                    height = all_possible_solutions[current_row]["height"]
                    width = all_possible_solutions[current_row]["width"]
                    thickness = all_possible_solutions[current_row]["thickness"]
                    results["min_required_profile"] = f"\u25AF{height}x{width}/{thickness}wall mm"
                

                results["area"] = all_possible_solutions[current_row]["area"]

                break

            else:
                # Else next row in database is examined
                current_row += 1
                # If this was last row then break
                if current_row == len(all_possible_solutions):
                    results["profile_found"] = False
                    break    

    # Else there is no possible solution in database
    else:
        results["profile_found"] = False
    
    return results

