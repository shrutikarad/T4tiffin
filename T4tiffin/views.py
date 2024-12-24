from django.shortcuts import render, redirect, get_object_or_404
from .models.students import StudentRegistration
from .models.standard import Standards
from django.http import HttpResponse, HttpResponseForbidden
from django.db import transaction
from .models.school import School
from .models.orders import Orders
from .models.qrcodes import Qrcodes
from .models.forgotpassword import forgotpassword
from django.contrib import messages
from datetime import date
from django.contrib.auth.hashers import make_password, check_password
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


# Create your views here.



def body(request):
    return render(request, 'base.html')


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    elif request.method == 'POST':
        postdata = request.POST
        student_name = postdata.get('student_name')
        parent_name = postdata.get('parent_name')
        parent_phone = postdata.get('phone')
        standard = postdata.get('standard')
        division = postdata.get('division')
        roll_no = postdata.get('roll_no')
        username = postdata.get('Username') 
        password = postdata.get('password')
        address = postdata.get('address')

        if not student_name or not parent_name or not parent_phone or not standard or not division or not roll_no or not username or not password:
            return redirect('signup', {'error': 'All fields are required!'})

        try:
            student = StudentRegistration.objects.create(
                student_name=student_name,
                parent_name=parent_name,
                parent_phone=parent_phone,
                standard=standard,
                division=division,
                username=username,
                roll_no = roll_no,
                actual_password=password,
                password=make_password(password),
                address=address
            )
            print("Student created:", student)

            same_encrypt1 = make_password(str(random.randint(10000, 99999)))  # Same value for encrypt1
            print("Same encrypt1 value:", same_encrypt1)

            for i in range(10):  # Create 10 rows with unique encrypt2
                encrypt2_value = make_password(str(random.randint(10000, 99999)))
                print(f"Creating QRCode {i+1}: encrypt1={same_encrypt1}, encrypt2={encrypt2_value}")
                
                Qrcodes.objects.create(
                    username=student,
                    encrypt1=same_encrypt1,
                    encrypt2=encrypt2_value
                )

            print("10 Qrcodes rows created successfully")

            Standards.objects.create(
                username=student,
                standard=standard
            )
            print("Standards created")

            messages.success(request, 'Registration Successful!')
            return redirect('signup')

        except Exception as e:
            print("Error occurred:", e)
            messages.error(request, 'An error occurred during registration.')
            return redirect('signup')




def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"Username: {username}, Password: {password}")

        # Attempt to get the school by username
        school = School().get_school_by_user(username)
        error_message = None

        if school:
            # Check if the password matches
            # flag1 = (password, school.password)
            flag = check_password(password, school.password)
            if flag:
                request.session['username'] = school.username
                b = messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                error_message = "Username or password is invalid!"
        else:
            # Attempt to get the student by username
            student = StudentRegistration().get_student_by_user(username)

            if student:
                # Check if the password matches
                flag = check_password(password, student.password)
                if flag:
                    # Store username in session after successful login
                    request.session['username'] = student.username
                    b = messages.success(request, 'Login successful!')
                    return redirect('parent_dashboard')  # Redirect to parent dashboard
                else:
                    error_message = "Username or password is invalid!"
            else:
                error_message = "Username or password is invalid!"

        print(f"Error: {error_message}")
        return render(request,'login.html', {'error': error_message})



def home(request):
    pending_orders_count = Orders.objects.filter(order_status='pending').count()  # Modify the filter according to your model's structure
    password_request = forgotpassword.objects.filter().count()
    return render(request, 'home.html', {'pending_orders_count': pending_orders_count, 'password_request' : password_request})


def orders(request):
    username = request.session.get('username')

    if username:
        # Check if the logged-in user is a school
        school = School.objects.filter(username=username).first()

        if school:
            # If the user is a school, show all orders
            orders = Orders.objects.all()
            return render(request, 'orders.html', {'orders': orders, 'is_student': False})

        else:
            # Handle case where the user is not a school (if needed)
            messages.error(request, 'Invalid user type!')
            return redirect('login')
    else:
        messages.warning(request, 'Please log in to view orders!')
        return redirect('login')



# View for updating order status (School Panel)
def update_order_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Orders, id=order_id)

        # Only school user can update order status
        username = request.session.get('username')
        school = School.objects.filter(username=username).first()

        if not school:
            messages.error(request, "You do not have permission to update the order status.")
            return redirect('orders')  # Redirect to orders page if not a school user

        # Get new status from form data
        new_status = request.POST.get('order_status')
        
        if new_status:
            order.order_status = new_status
            order.save()
            # messages.success(request, 'Order status updated successfully!')
        else:
            # messages.error(request, 'Invalid status.')
            pass
        
        # Redirect back to the orders page
        return redirect('orders')  # Redirect to orders page after updating status
    else:
        return HttpResponseForbidden("Invalid request method.")



def registered(request, standard_id=None):
    # Fetch all standards for the sidebar
    standards = Standards.objects.values_list('standard', flat=True).distinct()

    # Get selected standard from query params
    standard_name = request.GET.get('standard_id', None)  # Get from query params

    if standard_name:
        # Fetch students based on standard
        students = StudentRegistration.objects.filter(standard=standard_name)
    else:
        students = []

    context = {
        'standards': standards,
        'students': students,
    }
    return render(request, 'registered.html', context)



def parentsDashboard(request):
    return render(request, 'parent_dashboard.html')


def track_orders(request):
    return render(request, 'track_orders.html')


def place_order(request):
    if request.method == 'POST':
        username = request.session.get('username')
        
        if username:
            student = StudentRegistration.objects.get(username=username)
            
            if student:
                postdata = request.POST
                address = postdata.get('address')
                additional_note = postdata.get('additional_notes')
            

                code = str(random.randint(10000, 99999))
                
                encrypt = make_password(code)

                # Create a new order and save it
                order = Orders(username=student, address=address, additional_note=additional_note, code = code, encrypt = encrypt)
                order.save()

                print(encrypt)

                # Redirect to the view_orders page after placing the order
                c = messages.success(request, 'Your order has been placed successfully!')
                return redirect('view_orders')  # Redirect to view orders page
                
            else:
                messages.error(request, 'Student not found!')
        else:
            messages.warning(request, 'Please log in to place an order.')

    return render(request,'place_order.html')



  
        # #fetch the student data

        # try:
        #     student1 = StudentRegistration.objects.get(username = username)
            
        #     order = Orders(username=student1, address = address, additional_note = additional_note)
        #     order.save()

        #     messages.success(request, 'Your order has been placed successfully!')
        #     return render(request, 'parent_dashboard.html')
        # except:
        #     messages.success(request, 'Your order has been placed successfully!')
        #     return render(request, 'place_order.html')
    

def view_orders(request):
    username = request.session.get('username')
    
    if username:
        try:
            student = StudentRegistration.objects.get(username=username)
            
            # Fetch all orders for the student using filter
            orders = Orders.objects.filter(username=student)
            
            if orders.exists():
                return render(request, 'view_orders.html', {'orders': orders})
            else:
                e = messages.info(request, 'You have no orders placed yet.')
                return render(request, 'view_orders.html')
        
        except StudentRegistration.DoesNotExist:
            e = messages.error(request, 'Student not found!')
            return render(request, 'view_orders.html')
    
    else:
        messages.warning(request, 'Please log in to view your orders.')
        return render(request, 'login.html')


def contact(request):
    return render(request,'contact.html')

def logout(request):
    # Clear the session to log the user out
    if 'username' in request.session:
        del request.session['username']
        d = messages.success(request, 'Logged out successfully!')
    return render(request, 'login.html')  # Redirect to login page


def view_my_qr(request):
    username = request.session.get('username')  # Get the logged-in student's username from the session
    if not username:
        return redirect('login')  # Redirect to login if user is not logged in

    try:
        # Fetch the student's data using their username
        student = StudentRegistration.objects.get(username=username)
        order = Orders.objects.filter(username = student).order_by('-created_at').first()
        return render(request, 'view_my_qr.html', {'student': order})
    
    except StudentRegistration.DoesNotExist:
        # Handle case where student does not exist
        return render(request, 'view_my_qr.html', {'student': None})


def verify_user(request):
    user_details = None
    if request.method == 'POST':
        encrypt = request.POST.get('encrypt')
        if encrypt:
            try:
                user_data = Orders.objects.get(encrypt=encrypt)
                user_details = {
                    'student_name': user_data.username.student_name,
                    'parent_name': user_data.username.parent_name,
                    'standard': user_data.username.standard,
                    'division': user_data.username.division,
                    'parent_phone': user_data.username.parent_phone
                }
            except Orders.DoesNotExist:
                user_details = "User not found."
    return render(request, 'verify_user.html', {'user_details': user_details})


def forgotpass(request):
    if request.method == 'GET':
        return render(request, 'forgotpass.html')
    elif request.method == 'POST':
        postdata = request.POST
        student_name = postdata.get('student_name')
        mobile_number = postdata.get('mobile_no')
        standard = postdata.get('standard')
        division = postdata.get('division')
        roll_no = postdata.get('roll_no')

        if not student_name or not mobile_number or not standard or not division or not roll_no:
            messages.error(request, 'All fields are required!')
            return render(request, 'forgotpass.html')

        try:
            forpass = forgotpassword.objects.create(
                student_name=student_name,
                mobile_number=mobile_number,
                standard=standard,
                division=division,
                roll_no=roll_no,
            )
            forpass.save()

            messages.success(request, 'Your request has been submitted successfully!')
            return redirect('forgotpass')  # Redirect after successful submission

        except Exception as e:
            print("Error occurred:", e)
            messages.error(request, 'An error occurred during forgot password.')
            return render(request, 'forgotpass.html')

    # Explicit return statement for unexpected cases
    return render(request, 'forgotpass.html')






def startpage(request):
    return render(request, 'startpage.html')

def scanner(request):
    return render(request, 'cam.html')



def changepass(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        previous_password = request.POST.get('previous_password')
        new_password = request.POST.get('new_password')
        conform_password = request.POST.get('conform_password')

        # Check if user exists
        user = School.get_school_by_user(username)
        if not user:
            messages.error(request, "Invalid Username.")
            return redirect('/changepass')

        # Validate previous password
        if not (previous_password, user.password):
            messages.error(request, "Previous password is incorrect.")
            return redirect('/changepass')

        # Check if new password and confirm password match
        if new_password != conform_password:
            messages.error(request, "New password and Confirm password do not match.")
            return redirect('/changepass')

        # Hash the new password and update
        user.password = make_password(new_password)
        user.save()

        messages.success(request, "Password changed successfully!")
        return redirect('/changepass')

    return render(request, 'changepass.html')



@csrf_exempt  # If you're not using CSRF protection in this API endpoint, you can use this decorator
def get_student_details(request):
    if request.method == "POST":
        data = json.loads(request.body)
        encrypt2 = data.get("encrypt1")
        encrypt1 = data.get("encrypt2")

        # Debugging the received values
        print("Received encrypt1:", encrypt1)
        print("Received encrypt2:", encrypt2)

        # Check if both values exist
        if not encrypt1 or not encrypt2:
            return JsonResponse({'success': False, 'message': 'Invalid QR codes.'})

        try:
            # Search for the qr_code using encrypt2
            qr_code = Qrcodes.objects.get(encrypt2=encrypt2)
            print("QR Code found:", qr_code)

            # Now access the StudentRegistration through the ForeignKey 'username'
            student = qr_code.username  # This is the related student record

            # Compare encrypt1 (password) with stored value
            if qr_code.encrypt1 == encrypt1:  # Assuming 'encrypt1' is used for authentication
                student_details = {
                    'success': True,
                    'student_name': student.student_name,
                    'parent_name': student.parent_name,
                    'parent_phone': student.parent_phone,
                    'standard': student.standard,
                    'division': student.division,
                    'address': student.address,
                }
                return JsonResponse(student_details)
            else:
                print("Password does not match.")
                return JsonResponse({'success': False, 'message': 'QR codes do not match.'})

        except Qrcodes.DoesNotExist:
            print("QR code not found in database.")
            return JsonResponse({'success': False, 'message': 'QR code not found.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def passwordrequest(request):
    forgot_passwords = forgotpassword.objects.all()
    return render(request, 'passwordrequest.html', {'forgot_passwords': forgot_passwords})


def about(request):
    return render(request, 'about.html')

def profile(request):
    username = request.session.get('username')

    if username:
        try:
            student = StudentRegistration.objects.get(username = username)

            if student.isExist():
                return render(request, 'profile.html',{'student': student})

        except StudentRegistration.DoesNotExist:
            # Handle case where the student doesn't exist
            return render(request, 'profile.html', {'error': "Student not found."})

    else:
        # If no username found in session, redirect to login
        return redirect('login')  # Assuming you have a 'login' URL name set up



def schoolregistration(request):
    if request.method == 'GET':
        return render(request, 'schoolregistration.html')

    elif request.method == 'POST':
        postdata = request.POST

        school_name = postdata.get('school_name')
        username = postdata.get('username')
        password = postdata.get('password')

        # Check if school name or username already exists in the database
        if School.objects.filter(school_name=school_name).exists():
            messages.error(request, "School with this name already exists.")
            return redirect('schoolregistration')
        if School.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('schoolregistration')

        try:
            # Create a new school record and hash the password
            school = School.objects.create(
                school_name=school_name,
                username=username,
                password=make_password(password)
            )
            school.save()

            # Success message
            messages.success(request, "School registered successfully!")
            return redirect('login')  # Redirect to login page after successful registration

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('schoolregistration')