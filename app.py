from flask import Flask,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from flask_cors import CORS
from backend.helper_functions import get_db_connection,generate_otp,configure_app,send_email

app = Flask(__name__)

CORS(app)
configure_app(app)



@app.route("/signup",methods = ["POST"])
def signup():

    signup_data = request.get_json()
    if not signup_data:
        return jsonify({"error":"Bad request"}),400
    

    if "usertype" not in signup_data:
        return jsonify({"error":"Invalid Credentials"}),400
    
    usertype = signup_data.get('usertype')

    connection  = get_db_connection()
    cursor = connection.cursor()

    if usertype.lower() == "student":
        if "name" not in signup_data or "usn" not in signup_data or "email" not in signup_data or "password" not in signup_data:
            return jsonify({"error":"Missing Crdentials"}),400
    

        name = signup_data.get('name')
        usn = signup_data.get('usn')
        email = signup_data.get('email')
        password  = signup_data.get('password')
    
        cursor.execute("SELECT email,email_verified FROM students WHERE email = %s",(email,))
        result = cursor.fetchone()

        if result and result[1] == 1: #email exists and is verified
            connection.close()
            return jsonify({"error":"Account already exists"}),409
        
        elif result and result[1] == 0: #email already exists but not verified
            otp = generate_otp()
            cursor.execute("UPDATE otps SET otp = %s WHERE email = %s",(otp,email))
            connection.commit()
            connection.close()
            
            return jsonify({"success":"Account exists but isnt verified"}),401
            
            
        
        else:
            hash_password = generate_password_hash(password)
            otp = generate_otp()
            cursor.execute('''INSERT INTO students(name,usn,email,password,email_verified) 
                           VALUES(%s,%s,%s,%s,%s)''',(name,usn,email,hash_password,0))
            
            cursor.execute('''INSERT INTO otps(email,otp) 
                           VALUES(%s,%s)''',(email,otp))
            
            connection.commit()
            connection.close()

            send_email(app,email,otp)

            return jsonify({"success":"OTP has been sent successfully"}),200
        

    elif  usertype.lower() == "faculty":
        if "name" not in signup_data or "email" not in signup_data or "password" not in signup_data:
            return jsonify({"error":"Missing Crdentials"}),400
        
        name = signup_data.get('name')
        email = signup_data.get('email')
        password  = signup_data.get('password')
        

        cursor.execute("SELECT email,email_verified FROM faculties WHERE email = %s",(email,))
        

        result = cursor.fetchone()

        if result and result[1] == 1:
            connection.close()
            return jsonify({"error":"Account already exists"}),409
        
        elif result and result[1] == 0: #email already exists but not verified
            otp = generate_otp()
            cursor.execute("UPDATE otps SET otp = %s WHERE email = %s",(otp,email))
            connection.commit()
            connection.close()

        
            
            return jsonify({"success":"Account exists but isnt verified"}),401
        

        
        else:
            hash_password = generate_password_hash(password)
            otp = generate_otp()
            cursor.execute('''INSERT INTO faculties(name,email,password,email_verified,otp) 
                           VALUES(%s,%s,%s,%s,%s)''',(name,email,hash_password,0,otp))
            
                  
            cursor.execute('''INSERT INTO otps(email,otp) 
                           VALUES(%s,%s)''',(email,otp))
            
            connection.commit()
            connection.close()

            send_email(app,email,otp)

            
        
            return jsonify({"success":"OTP has been sent successfully"}),200
        


@app.route("/verify_email",methods = ["POST"])
def verify_email():
    data = request.get_json()
    if not data:
        return jsonify({"error":"Bad request"}),400
    
    if "email" not in data or "otp" not in data or "usertype" not in data:
        return jsonify({"error":"Invalid credentials"}),400
    
    connection = get_db_connection()
    cursor = connection.cursor()

    email = data.get('email')
    otp = data.get('otp')
    usertype = data.get('usertype')

    if usertype.lower() == "student":
        cursor.execute("SELECT email,email_verified FROM students WHERE email  = %s",(email,))
        result = cursor.fetchone()

        if result and result[1] == 1:
            connection.close()
            return jsonify({"error":"Email already verified"}),200
        
        if not result:
            return jsonify({"error":"Account not found"}),404
        

        
        elif result and result[1] == 0:
            cursor.execute("SELECT email,otp FROM otps WHERE email = %s",(email,))
            result_2 = cursor.fetchone()

            if result_2 and result_2[1]:
                stored_otp = result_2[1]
                
                if otp == stored_otp:
                    cursor.execute("UPDATE students SET email_verified = %s WHERE email = %s",(1,email))
                    cursor.execute("DELETE email,otp FROM otps WHERE email = %s",(email,))

                    connection.commit()
                    connection.close()
                    return jsonify({"success":"OTP verified Succesfully"}),200
                else:
                    return jsonify({"error":"Invalid OTP"}),400
                
        else:
            return jsonify({"error":"re-authentication required"}),401
        
    elif usertype.lower() == "faculty":
        cursor.execute("SELECT email,email_verified FROM faculties WHERE email  = %s",(email,))
        result = cursor.fetchone()

        if result and result[1] == 1:
            connection.close()
            return jsonify({"error":"Email already verified"}),200
        
        if not result:
            return jsonify({"error":"Account not found"}),404
        

        
        elif result and result[1] == 0:
            cursor.execute("SELECT email,otp FROM otps WHERE email = %s",(email,))
            result_2 = cursor.fetchone()

            if result_2 and result[1]:
                stored_otp = result[1]
                
                if otp == stored_otp:
                    cursor.execute("UPDATE faculties SET email_verified = %s WHERE email = %s",(1,email))
                    cursor.execute("DELETE  FROM email,otp FROM otps WHERE email = %s",(email,))

                    connection.commit()
                    connection.close()
                    return jsonify({"success":"OTP verified Succesfully"}),200
                else:
                    return jsonify({"error":"Invalid OTP"}),400
                
        else:
            return jsonify({"error":"re-authentication required"}),401
    else:
        return jsonify({"error":"Invalid user type"}),400
        


@app.route("/resend_otp",methods = ["POST"])
def resend_otp():
    data = request.get_json()

    if not data:
        return jsonify({"error":"Bad request"}),400
    
    if "email" not in data or "usertype" not in data:
        return jsonify({"error":"Missing credntials"}),400
    
    email = data.get('email')
    usertype = data.get('usertype')
    
    
    new_otp = generate_otp()

    connection = get_db_connection()

    cursor = connection.cursor()

    if usertype.lower() == "student":
        cursor.execute("SELECT email,email_verified FROM students WHERE email = %s",(email,))

        result = cursor.fetchone()
        if result and result[1] == 1: # if email already exists and is already verified in student table, reject the request
            connection.close()
            return jsonify({"error":"Email already exists"}),409
        
        elif result and result[1] == 0: # if email already exists and is not verified in student table, check if email is in otps table

            cursor.execute("SELECT email FROM otps WHERE email = %s",(email,))
            result_2 = cursor.fetchone()

            if result_2: # if email exists then update the old_otp to newly genrated otp
                cursor.execute("UPDATE otps SET otp = %s WHERE email = %s",(new_otp,email))
                connection.commit()
                connection.close()
                return jsonify({"success":"otp resent successfully"}),200
            
            else: # if email doesnt exist in otp table then insert and resend otp

                cursor.execute("INSERT INTO otps(email,otp) VALUES(%s,%s)",(email,new_otp))
                connection.commit()
                connection.close()
                send_email(app,email,new_otp)

               


                return jsonify({"success":"OTP resent succesfully"}),200
        
    elif usertype.lower() == "faculty":
        cursor.execute("SELECT email,email_verified FROM faculties WHERE email = %s",(email,))

        result = cursor.fetchone()
        if result and result[1] == 1: # if email already exists and is already verified in student table, reject the request
            connection.close()
            return jsonify({"error":"Email already exists"}),409
        
        elif result and result[1] == 0: # if email already exists and is not verified in student table, check if email is in otps table

            cursor.execute("SELECT email FROM otps WHERE email = %s",(email,))
            result_2 = cursor.fetchone()

            if result_2: # if email exists then update it old_otp to newly genrated otp
                cursor.execute("UPDATE otps SET otp = %s WHERE email = %s",(new_otp,email))
                connection.commit()
                connection.close()
                return jsonify({"success":"otp resent successfully"}),200
            
            else: # if email doesnt exist in otp table then insert and resend otp

                cursor.execute("INSERT INTO otps(email,otp) VALUES(%s,%s)",(email,new_otp))
                connection.commit()
                connection.close()
                send_email(app,email,new_otp)

                return jsonify({"success":"Email resent succesfully"}),200
            
    else:
        connection.close()
        return jsonify({"error":"Invalid user type"}),400
            
        
if __name__ == "__main__":
    app.run(debug = True)
