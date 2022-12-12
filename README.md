# **Section Calculator Web Application**

## Fully functional app for solving basic elements of structure problems

Application which calculate dimensions of desired sections amongst many standard structural elements based on combinations of basic structural loads and material choice. Application also gives possibilty of calculating best possible solution for specific cases. Application have these major specifications:

* Functional register and login validation
* User data (changing password, adding more credits etc)
* Calculating standard dimension for the desired cross-section, loading type combination, material property and safety factor
* Giving best possible solution - cross-section with smallest possible area - which means cheapest structural element for the same specific loading values and material
* Tracking user available credit needed for calculation and optimization

## **How To Use App**
Instructions on how to use application is fully shown in the video from the [LINK](https://pages.github.com/).

## **Technical Specifications**
Design of the web application was heavly based on the Bootstrap template created by [Arsha](https://bootstrapmade.com/arsha-free-bootstrap-html-template-corporate/). There are certain changes in the design using Bootstrap 5 and CSS, and some additional JavaScript features implemented by author which will be mentioned. Regarding to the HTML, all pages are created by author except homepage.

Backend development was the main focus of this project, which is made in Python 3, in the Flask framework. This application posses three major parts done in Flask:
1. User authentication
2. Calculation and optimization engine
3. Backend caching

### **User Authentication**
In order to calculations to be preformed, user have to be registred and logined.
**Register** have next specifications:
- Form requires unique username (database will be searched with filled username)
- Username needs to have at least 4 characters
- Password needs to have at least 8 characters with at least one digit
- Password is hashed and salted before stored in databse
- Every new user gets 10 credits for free

After successful registration **login** can be preformed which have next specifications:
- Checking whether user exists in the database if not, program redirects to the /register route
- Checking the password if user exists but password was not correct it redirect to the login form but with filled username
- If user successfully logined, in cache user's id, username and credits data from the database is being saved

User can preform certain tasks regarding to his profile:
- Changing password
- Adding credits which simulate buying credits or upgrading to the premium benefits
- Log out


### **Calculating Engine**
Every subsuquent step requires logged user. Also every step in calculation depends on the previous steps which will be covered in last section of this paragraph. To even start journey of calculating user needs to have at least 1 credit which is the amount for the one calculation.

- First step - loading type is chosen. From the Mechanics, basic and most important and relevant loading types are axial loading, bending and torsion which appear in many and most structural elements,
- Second step - regarding on chosen loading type, its maximum value(s) needs to be specified and typed into the form,
- Third step - after maximum internal load values are specified, now it is time to give informations about used material. Tensile strength or yield strength is required with safety factor. Allowable normal stress is then tensile strength or yield strength divided by safety factor.
- Fourth step - chosing desired cross section. There are 8 of them in the app (I, U and T channel, as well as round, squre and rectangle tube and square and round bar). If there are torsion rotation is applied so there is common sense that only round section can be chosen (round bar or round tube) and that is solved in app. 
 - Fifth step - calculating required dimension. This is the most complex step because there are possibly two types of stress. Axial loading and bending causes normal stress (two subsequent points are moving from each other or toward each other due to the load) and tangential stress which cause slipping of two subsequent points. These stresses can be combined and presented as equivalent normal stress via [Von-Mises formulation](https://en.wikipedia.org/wiki/Von_Mises_yield_criterion) and be checked against allowable normal stress. Regarding whether only axial loading exits, bending or combined axial and bending there is only normal stress so it needs to calculate required cross-sectional area or moment of inertia Wx and choose amongs standard dimensions from the cross-sectional databases. If torsion exits then only round section can be chosen, so required diameter is calculated, and after that required moment of inertia Wx, and first standard profile from the database is selected. After that always stress in the chosen cross-section is checked against allowable stress and if it is greater than allowable, next profile is chosen and stress checking is repeated as long as this condition is not satisifed. At the end if there is possible desired standard cross-section, it will be written in the page with the summary of chosen data, else user will be notified that no existing desired standard cross-section can be possibly chosen.
 - (Optional) Sixth step - optimization. If user chose this step, app will calculate best possible solution amongst all of the given cross-sections. This means that lightest possible structural element (one with the smallest cross-sectional area) will be presented to the user, so expenses can be seized by using this cross-section for the same loading values and chosen material.

 ### **Backend caching**
 TODO


## **Needs To Be Done**
- Sending e-mail in the contact section of the home page
- Tracking calculations, optimizations and purchases history
- Implementing upgrade and buying credits for calculation using real credit cards and/or PayPal etc.
- Instead of the providing maximum internal loads, it would be nice for app to calculate those values knowing external/applied loads onto the structure
- Instead of providing values for tensile/yield strength it would be better to provide user to choose amongst standard materials which is already exists with its values already specified

## **Contact**
Any information, bugs or questions can be sent on the e-mail adress: i.zejd@hotmail.com

