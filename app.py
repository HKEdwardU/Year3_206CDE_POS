from flask import Flask, render_template, request, redirect, session
from tabulate import tabulate
from email_validator import validate_email
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'ABCDE'

SQL_File = input('Enter the SQL File location:')
conn = sqlite3.connect(SQL_File, check_same_thread=False)
cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        Staff_ID = request.form['Staff_ID']
        password = request.form['password']

        Sql = "Select Staff_PW, Staff_Name, Admin_Auth From Staff Where Staff_ID = '{0}'".format(Staff_ID)
        cur.execute(Sql)
        myresult = cur.fetchone()

        if myresult:
            if myresult[0] == password:
                session['User_ID'] = Staff_ID
                session['User_Name'] = myresult[1]
                session['Admin_Auth'] = myresult[2]
                session['Error_Message'] = ''
                session['C_ID'] = ''
                session['M_Error'] = ''
                return redirect('/Total_Price')
            else:
                message = "Wrong User's name or password, please enter again!"
                return render_template('Login.html', SignInM = message)
        else:
            message = "Wrong User's name or password, please enter again!"
            return render_template('Login.html', SignInM = message)

    return render_template('Login.html', SignInM = '')

@app.route('/POS', methods=['GET', 'POST'])
def index():
    User_Name = session['User_Name']
    session['Error_Message'] = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            P_ID = request.form['Find_PID']
            
            Sql = "Select Size_ID, P_Name, Price From Product Where P_ID = '{0}'".format(P_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            
            if myresult:
                Sql = "Select * From Cart Where P_ID = '{0}'".format(P_ID)
                cur.execute(Sql)
                Cart_Found = cur.fetchone()
                if Cart_Found:
                    Sql = "Update Cart Set P_Qty = P_Qty + 1 Where P_ID = '{0}'".format(P_ID)
                    cur.execute(Sql)
                    conn.commit()
                    return redirect('/Total_Price')
                else:
                    Product_Info = {}
                    Product_Info[0] = myresult[0]
                    Product_Info[1] = '1'
                    Product_Info[2] = myresult[2]
                    Sql = "Insert Into cart (P_ID, Size_ID, P_Qty, Price) Values ('{0}','{1}','{2}','{3}')".format(P_ID,Product_Info[0],Product_Info[1],Product_Info[2])
                    cur.execute(Sql)
                    conn.commit()
                    return redirect('/Total_Price')
            else:
                session['Error_Message'] = 'Error: wrong product ID, please enter again!'
                return redirect('/Cart_Table')
        elif Function_ID == '2':
            C_ID = request.form['Find_CID']
            if C_ID != '':
                Sql = "Select * From Customers Where C_ID = '{0}'".format(C_ID)
                cur.execute(Sql)
                myresult = cur.fetchone()
                if myresult:
                    session['C_ID'] = C_ID
                    session['M_Error'] = 'Login as'+ C_ID
                else:
                    session['M_Error'] = 'Unable to find the menber, please enter again!'
            return redirect('/Cart_Table')

    T_Price = 0
    return render_template('POS.html', Total_Price = T_Price, User_Name = User_Name)

@app.route('/Delete', methods=['GET', 'POST'])
def Delete():
    if request.method == 'POST':
        message = ''
        P_ID = request.form['Find_PID']
        D_Num = request.form['Num']

        Sql = "Select * From Cart Where P_ID = '{0}'".format(P_ID)
        cur.execute(Sql)
        myresult = cur.fetchone()

        if myresult:
            if D_Num == '':
                Sql = "Delete From Cart Where P_ID = '{0}'".format(P_ID)
                cur.execute(Sql)
                conn.commit()
                return redirect('/Total_Price')
            else:
                Sql = "Select (P_Qty - {1}) From Cart Where P_ID = '{0}'".format(P_ID,D_Num)
                cur.execute(Sql)
                Num = cur.fetchone()
                if Num[0] <= 0:
                    Sql = "Delete From Cart Where P_ID = '{0}'".format(P_ID)
                else:
                    Sql = "Update Cart Set P_Qty = P_Qty - '{0}' Where P_ID = '{1}'".format(D_Num,P_ID)
                cur.execute(Sql)
                conn.commit()
                return redirect('/Total_Price')
        else:
            message = 'Product not found'
            return render_template('POS.html', Delete_Message = message)

@app.route('/Cart_Table')
def Cart_Table():
    User_Name = session['User_Name']
    Sql = "Select Cart.P_ID, Cart.Size_ID, Product.P_Name, Cart.Price, Cart.P_Qty, (Cart.Price*Cart.P_Qty) AS Total_Price From Cart join Product where Cart.P_ID = Product.P_ID"
    cur.execute(Sql)
    Product_Table = []
    for row in cur:
        Product_Table.append(row)
    CartTable = tabulate(Product_Table, tablefmt='html')
    Total_Price = session['T_Price']
    Error_Message = session['Error_Message']
    M_Error = session['M_Error']
    return render_template('POS.html', CartTable = CartTable, Total_Price = Total_Price, User_Name = User_Name, Error_Message = Error_Message, M_Error = M_Error)
    

@app.route('/Total_Price')
def Total_Price():
    Sql = "Select sum(P_Qty*Price) From Cart"
    cur.execute(Sql)
    myresult = cur.fetchone()
    if myresult:
        T_Price = myresult[0]
        if T_Price == None:
            session['T_Price'] = 0
            return redirect('/Cart_Table')
        else:
            session['T_Price'] = T_Price
            return redirect('/Cart_Table')

@app.route('/Cancel', methods=['GET', 'POST'])
def Cancel():
    Sql = "Delete From Cart"
    cur.execute(Sql)
    conn.commit()
    session['M_Error'] = ''
    session['C_ID'] = ''
    return redirect('/Total_Price')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    User_Name = session['User_Name']
    if request.method == 'POST':

        if session['C_ID'] != '':
            C_ID = session['C_ID']
        else:
            C_ID = ''
        PM_Code = request.form['PM_Code']
        if PM_Code != '':
            Sql = "Select PM_Discount_Value From Promotion Where PM_Code = '{0}'".format(PM_Code)
            cur.execute(Sql)
            DC_Value = cur.fetchone()[0]
        else:
            DC_Value = ''

        Sql = "Select Staff_ID From Staff Where Staff_Name = '{0}'".format(User_Name)
        cur.execute(Sql)
        User_ID = cur.fetchone()[0]
        Sql = "Select P_ID, Size_ID, P_Qty, (Price*P_Qty) from Cart"
        cur.execute(Sql)
        myresult = cur.fetchall()

        for row in myresult:
            Sql = "Update Inventory Set I_Qty = I_Qty - '{0}' Where P_ID = '{1}'".format(row[2],row[0])
            cur.execute(Sql)
            conn.commit()
            Sql = "Select (Max(R_ID) + 1) From record"
            cur.execute(Sql)
            myresult = cur.fetchone()[0]
            if myresult == None:
                new_R_ID = '1'
            else:
                new_R_ID = myresult
            if new_R_ID == '':
                new_R_ID = '1'
            new_R_Date = datetime.now().date()
            if DC_Value != '':
                Sql = "Insert Into record (R_ID, C_ID, SF_ID, P_ID, Size_ID, P_Qty, Total_Price, Date) Values ('{0}','{1}','{2}','{3}','{4}','{5}',({6} * {7}),'{8}')".format(new_R_ID,C_ID,User_ID,row[0], row[1], row[2], row[3],DC_Value,new_R_Date)
            else:
                Sql = "Insert Into record (R_ID, C_ID, SF_ID, P_ID, Size_ID, P_Qty, Total_Price, Date) Values ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(new_R_ID,C_ID,User_ID,row[0], row[1], row[2], row[3],new_R_Date)
            cur.execute(Sql)
            conn.commit()
            if C_ID != '':
                Sql = "Update Customers Set M_Point = M_Point + '{0}' Where C_ID = '{1}'".format(row[3],C_ID)
                cur.execute(Sql)
                conn.commit()

        return render_template('Complete.html', User_Name = User_Name)

    Sql = "Select * From Cart"
    cur.execute(Sql)
    Empty_Cart = cur.fetchone()
    if Empty_Cart:
        return render_template('Payment.html')
    else:
        return redirect('/Total_Price')

@app.route('/Inventory', methods=['GET', 'POST'])
def Inventory():
    User_Name = session['User_Name']
    if request.method == 'POST':
        P_ID = request.form['Find_PID']
        if P_ID == '':
            Sql = "Select Inventory.P_ID, Inventory.Size_ID, Product.P_Name, Inventory.I_Qty From Inventory join Product where Inventory.P_ID = Product.P_ID"
        else:
            Sql = "Select Inventory.P_ID, Inventory.Size_ID, Product.P_Name, Inventory.I_Qty From Inventory join Product where Inventory.P_ID = Product.P_ID and Inventory.P_ID = '{0}'".format(P_ID)
    else:
        Sql = "Select Inventory.P_ID, Inventory.Size_ID, Product.P_Name, Inventory.I_Qty From Inventory join Product where Inventory.P_ID = Product.P_ID"
    cur.execute(Sql)
    Inventory_Table = []
    for row in cur:
        Inventory_Table.append(row)
    Invent_Table = tabulate(Inventory_Table, tablefmt='html')
    return render_template('Inventory.html', Invent_Table = Invent_Table, User_Name = User_Name)

@app.route('/management')
def management():
    User_Name = session['User_Name']
    Admin_Auth = session['Admin_Auth']
    if Admin_Auth == 'T':
        return render_template('management.html', User_Name = User_Name)
    else:
        return redirect('/Temp_Auth')
    return render_template('management.html', User_Name = User_Name)


@app.route('/Temp_Auth', methods=['GET', 'POST'])
def Temp_Auth():
    if request.method == 'POST':
        Staff_ID = request.form['Staff_ID']
        password = request.form['password']
        Sql = "Select Staff_PW, Admin_Auth From Staff Where Staff_ID = '{0}'".format(Staff_ID)
        cur.execute(Sql)
        myresult = cur.fetchone()

        if myresult[0] == password and myresult[1] == 'T':
            return render_template('management.html')
        else:
            message = "Wrong User's name or password / This user don't have authority, please enter again!"
            return render_template('Temp_Auth.html', SignInM = message)
    return render_template('Temp_Auth.html')

@app.route('/Record', methods=['GET', 'POST'])
def Record():
    User_Name = session['User_Name']
    Update_message = ''
    Delete_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            Update_RID = request.form['Update_RID']
            Sql = "Select C_ID, SF_ID, P_ID, Size_ID, P_Qty From record Where R_ID = '{0}'".format(Update_RID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                myresult_list = list(myresult)
                Update_CID = request.form['Update_CID']
                Update_SFID = request.form['Update_SFID']
                Update_PID = request.form['Update_PID']
                Update_SID = request.form['Update_SID']
                Update_Qty = request.form['Update_Qty']
                if Update_CID != '':
                    myresult_list[0] = Update_CID
                if Update_SFID != '':
                    myresult_list[1] = Update_SFID
                if Update_PID != '':
                    myresult_list[2] = Update_PID
                if Update_SID != '':
                    myresult_list[3] = Update_SID
                if Update_Qty != '':
                    myresult_list[4] = Update_Qty
                Sql = "Select Price From Product Where P_ID = '{0}'".format(myresult_list[2])
                cur.execute(Sql)
                Update_Price = cur.fetchone()[0]
                Total_Price = int(myresult_list[4]) * Update_Price
                Sql = "Update record Set C_ID = '{0}', SF_ID = '{1}', P_ID = '{2}', Size_ID = '{3}', P_Qty = '{4}', Total_Price = '{5}'  Where R_ID = '{6}'".format(myresult_list[0],myresult_list[1],myresult_list[2],myresult_list[3],myresult_list[4],Total_Price,Update_RID)
                cur.execute(Sql)
                conn.commit()
                Update_message = 'Product Update successfully!'
            else:
                Update_message = 'Unable to find the product, please enter again'
        elif Function_ID == '2':
            Find_RID = request.form['Find_RID']
            Sql = "Select * From record Where R_ID = '{0}'".format(Find_RID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From record Where R_ID = '{0}'".format(Find_RID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Refund success!'
            else:
                Delete_message = 'Unable to find the record, please enter again!'
    Sql = "Select * From Record"
    cur.execute(Sql)
    Record_Table = []
    for row in cur:
        Record_Table.append(row)
    Record_Table = tabulate(Record_Table, tablefmt='html')
    return render_template('Record.html', Record_Table = Record_Table, Delete_message = Delete_message, Update_message = Update_message, User_Name = User_Name)

@app.route('/Product_List', methods=['GET', 'POST'])
def Product_List():
    User_Name = session['User_Name']
    message = ''
    Delete_message = ''
    Update_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            New_PID = request.form['New_PID']
            Sql = "Select * From Product Where P_ID = '{0}'".format(New_PID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                message = 'You are using a ID that had been used, enter a different one!'
            else:
                New_SizeID = request.form['New_SizeID']
                New_P_Name = request.form['New_P_Name']
                New_Price = request.form['New_Price']
                Sql = "Insert Into Product Values ('{0}','{1}','{2}','{3}')".format(New_PID,New_SizeID,New_P_Name,New_Price)
                cur.execute(Sql)
                conn.commit()
                Sql = "Insert Into Inventory Values ('{0}','{1}',0)".format(New_PID,New_SizeID)
                cur.execute(Sql)
                conn.commit()
                message = 'Product added successfully!'
        elif Function_ID == '2':
            Delete_PID = request.form['Delete_PID']
            Sql = "Select * From Product Where P_ID = '{0}'".format(Delete_PID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From Product Where P_ID = '{0}'".format(Delete_PID)
                cur.execute(Sql)
                conn.commit()
                Sql = "Delete From Inventory Where P_ID = '{0}'".format(Delete_PID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Product Delete successfully!'
            else:
                Delete_message = 'Unable the find the product, please enter again!'
        elif Function_ID == '3':
            Update_PID = request.form['Update_PID']
            Sql = "Select * From Product Where P_ID = '{0}'".format(Update_PID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                myresult_list = list(myresult)
                Update_SizeID = request.form['Update_SizeID']
                Update_P_Name = request.form['Update_P_Name']
                Update_Price = request.form['Update_Price']
                if Update_SizeID != '':
                    myresult_list[1] = Update_SizeID
                    Sql = "Update Inventory Set Size_ID = '{0}'".format(Update_SizeID)
                    cur.execute(Sql)
                    conn.commit()
                if Update_P_Name != '':
                    myresult_list[2] = Update_P_Name
                if Update_Price != '':
                    myresult_list[3] = Update_Price
                Sql = "Update Product Set Size_ID = '{0}', P_Name = '{1}', Price = '{2}'  Where P_ID = '{3}'".format(myresult_list[1],myresult_list[2],myresult_list[3],Update_PID)
                cur.execute(Sql)
                conn.commit()
                Update_message = 'Product Update successfully!'
            else:
                Update_message = 'Unable to find the product, please enter again!'
    Sql = "Select * From Product"
    cur.execute(Sql)
    Product_List_Table = []
    for row in cur:
        Product_List_Table.append(row)
    Product_List_Table = tabulate(Product_List_Table, tablefmt='html')
    return render_template('Product_List.html', Product_List_Table = Product_List_Table, message = message, Delete_message = Delete_message, Update_message = Update_message, User_Name = User_Name)

@app.route('/Inventory_Refill', methods=['GET', 'POST'])
def Inventory_Refill():
    User_Name = session['User_Name']
    message = ''
    Update_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            Add_I_PID = request.form['Add_I_PID']
            Sql = "Select * From Inventory Where P_ID = '{0}'".format(Add_I_PID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Refill_Value = request.form['Refill_Value']
                Sql = "Update Inventory Set I_Qty = I_Qty + '{0}' Where P_ID = '{1}'".format(Refill_Value,Add_I_PID)
                cur.execute(Sql)
                conn.commit()
                message = 'Inventory update successfully!'
            else:
                message = 'Unable to find the product, please enter again!'
        elif Function_ID == '2':
            Update_I_PID = request.form['Update_I_PID']
            Sql = "Select * From Inventory Where P_ID = '{0}'".format(Update_I_PID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Update_Value = request.form['Update_Value']
                Sql = "Update Inventory Set I_Qty = '{0}' Where P_ID = '{1}'".format(Update_Value,Update_I_PID)
                cur.execute(Sql)
                conn.commit()
                Update_message = 'Update successfully!'
            else:
                Update_message = 'Unable to find the product, please enter again!'
    Sql = "Select Inventory.P_ID, Inventory.Size_ID, Product.P_Name, Inventory.I_Qty From Inventory join Product where Inventory.P_ID = Product.P_ID"
    cur.execute(Sql)
    Inventory_Table = []
    for row in cur:
        Inventory_Table.append(row)
    Invent_Table = tabulate(Inventory_Table, tablefmt='html')
    return render_template('Inventory_Refill.html', Invent_Table = Invent_Table, message = message, Update_message = Update_message, User_Name = User_Name)

@app.route('/Sales_Data_Product', methods=['GET', 'POST'])
def Sales_Data():
    User_Name = session['User_Name']
    Sql = "Select Product.P_ID, Product.Size_ID,  Product.P_Name, Product.Price, sum(record.P_Qty), Sum(record.Total_Price) From Product Join record Where Product.P_ID = record.P_ID Group by Product.P_ID"
    cur.execute(Sql)
    Data_Table = []
    for row in cur:
        Data_Table.append(row)
    Data_Table = tabulate(Data_Table, tablefmt='html')
    return render_template('Sales_Data.html', Data_Table = Data_Table, User_Name = User_Name)

@app.route('/Sales_Data_Day', methods=['GET', 'POST'])
def Sales_Data_Day():
    User_Name = session['User_Name']
    Sql = "Select strftime('%m', Date), Sum(P_Qty), Sum(Total_Price) From record Group By strftime('%m', Date) Order By strftime('%m', Date)"
    cur.execute(Sql)
    Data_Table = []
    for row in cur:
        Data_Table.append(row)
    Data_Table = tabulate(Data_Table, tablefmt='html')
    return render_template('Sales_Data_per_Day.html', Data_Table = Data_Table, User_Name = User_Name)

@app.route('/Promotion', methods=['GET', 'POST'])
def Promotion():
    User_Name = session['User_Name']
    message = ''
    Delete_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            New_PM_ID = request.form['New_PM_ID']
            Sql = "Select * From Promotion Where PM_ID = '{0}'".format(New_PM_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                message = 'You are using a promotion ID that had been used, please enter a different ID!'
            else:
                New_PM_Code = request.form['New_PM_Code']
                New_DC_Value = request.form['New_DC_Value']
                Sql = "Insert Into Promotion Values ('{0}','{1}','{2}')".format(New_PM_ID,New_PM_Code,New_DC_Value)
                cur.execute(Sql)
                conn.commit()
                message = 'Promotion Code added successfully!'
        elif Function_ID == '2':
            Delete_PM_ID = request.form['Delete_PM_ID']
            Sql = "Select * From Promotion Where PM_ID = '{0}'".format(Delete_PM_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From Promotion Where PM_ID = '{0}'".format(Delete_PM_ID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Promotion Code deleted successfully!'
            else:
                Delete_message = 'Unable to find promotion code, please enter again!'
    Sql = "Select PM_ID, PM_Code, PM_Discount_Value From Promotion"
    cur.execute(Sql)
    Promotion_Table = []
    for row in cur:
        Promotion_Table.append(row)
    Promotion_Table = tabulate(Promotion_Table, tablefmt='html')
    return render_template('Promotion.html', Promotion_Table = Promotion_Table, message = message, Delete_message = Delete_message, User_Name = User_Name)

@app.route('/Staff', methods=['Get', 'POST'])
def Staff():
    User_Name = session['User_Name']
    message = ''
    Delete_message = ''
    Update_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            New_Staff_ID = request.form['New_Staff_ID']
            Sql = "Select * From Staff Where Staff_ID = '{0}'".format(New_Staff_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                message = 'You are using a staff ID that had been used, please enter a different one!'
            else:
                New_Staff_Name = request.form['New_Staff_Name']
                New_Staff_PW = request.form['New_Staff_PW']
                New_Admin_Auth = request.form['New_Admin_Auth']
                Sql = "Insert Into Staff Values ('{0}','{1}','{2}','{3}')".format(New_Staff_ID,New_Staff_Name,New_Staff_PW,New_Admin_Auth)
                cur.execute(Sql)
                conn.commit()
                message = 'Staff added successfully!'
        elif Function_ID == '2':
            Delete_Staff_ID = request.form['Delete_Staff_ID']
            Sql = "Select * From Staff Where Staff_ID = '{0}'".format(Delete_Staff_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From Staff Where Staff_ID = '{0}'".format(Delete_Staff_ID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Staff infomation remove successfully!'
            else:
                Delete_message = 'Unable to find staff, please enter again!'
        elif Function_ID == '3':
            Update_Staff_ID = request.form['Update_Staff_ID']
            Sql = "Select * From Staff Where Staff_ID = '{0}'".format(Update_Staff_ID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                myresult_list = list(myresult)
                Update_Staff_Name = request.form['Update_Staff_Name']
                Update_Staff_PW = request.form['Update_Staff_PW']
                Update_Staff_Auth = request.form['Update_Staff_Auth']
                if Update_Staff_Name != '':
                    myresult_list[1] = Update_Staff_Name
                if Update_Staff_PW != '':
                    myresult_list[2] = Update_Staff_PW
                if Update_Staff_Auth != '':
                    myresult_list[3] = Update_Staff_Auth
                Sql = "Update Staff Set Staff_Name = '{0}', Staff_PW = '{1}', Admin_Auth = '{2}'  Where Staff_ID = '{3}'".format(myresult_list[1],myresult_list[2],myresult_list[3],Update_Staff_ID)
                cur.execute(Sql)
                conn.commit()
                Update_message = 'Staff information Update successfully!'
            else:
                Update_message = 'Unable to find the staff, Please enter again!'
    Sql = "Select * From Staff"
    cur.execute(Sql)
    Staff_Table = []
    for row in cur:
        Staff_Table.append(row)
    Staff_Table = tabulate(Staff_Table, tablefmt='html')
    return render_template('Staff.html', Staff_Table = Staff_Table, message = message, Delete_message = Delete_message, Update_message = Update_message, User_Name = User_Name)

@app.route('/Booking', methods=['Get','POST'])
def Booking():
    User_Name = session['User_Name']
    message = ''
    Delete_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            New_B_CID = request.form['New_B_CID']
            Sql = "Select * From Customers Where C_ID = '{0}'".format(New_B_CID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                New_B_PID = request.form['New_B_PID']
                Sql = "Select * From Product Where P_ID = '{0}'".format(New_B_PID)
                cur.execute(Sql)
                myresult = cur.fetchone()
                if myresult:
                    New_B_Qty = request.form['New_B_Qty']
                    if New_B_Qty > '0':
                        Sql = "Select (Max(B_ID) + 1) From Booking"
                        cur.execute(Sql)
                        New_BID = cur.fetchone()[0]
                        Sql = "Insert Into Booking Values ('{0}','{1}','{2}','{3}')".format(New_BID,New_B_CID,New_B_PID,New_B_Qty)
                        cur.execute(Sql)
                        conn.commit()
                        message = 'Booking added successfully!'
                    else:
                        message = 'Wrong booking number, please enter again!'
                else:
                    message = 'Wrong product ID, please enter again!'
            else:
                message = 'Wrong customer ID, please enter again!'
        elif Function_ID == '2':
            D_BID = request.form['D_BID']
            Sql = "Select * From Booking Where B_ID = '{0}'".format(D_BID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From Booking Where B_ID = '{0}'".format(D_BID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Record deleted successfully!'
            else:
                Delete_message = 'Unable to find the record, please enter again!'
    Sql = "Select Booking.B_ID, Booking.C_ID, Booking.P_ID, Product.P_Name, Booking.B_Qty From Booking Join Product Where Booking.P_ID = Product.P_ID"
    cur.execute(Sql)
    Booking_Table = []
    for row in cur:
        Booking_Table.append(row)
    Booking_Table = tabulate(Booking_Table, tablefmt='html')
    return render_template('Booking.html', Booking_Table = Booking_Table, message = message, Delete_message = Delete_message, User_Name = User_Name)

@app.route('/Membership', methods=['Get', 'POST'])
def Membership():
    User_Name = session['User_Name']
    message = ''
    Update_message = ''
    Delete_message = ''
    if request.method == 'POST':
        Function_ID = request.form['Function_ID']
        if Function_ID == '1':
            New_M_CName = request.form['New_M_CName']
            New_M_Email = request.form['New_M_Email']
            New_M_PW = request.form['New_M_PW']
            New_M_gender = request.form['New_M_gender']
            New_M_PNum = request.form['New_M_PNum']
            New_M_address = request.form['New_M_address']
            try:
                valid = validate_email(New_M_Email)
            except ValueError as e:
                message = 'Unvalid Email address, please enter again.'
            else:
                Sql = "Select (Max(C_ID) + 1) From Customers"
                cur.execute(Sql)
                New_CID = cur.fetchone()[0]
                Sql = "Insert Into Customers (C_ID, C_Name, C_Email, C_Password, gender, Phone_Num, Address) Values ('{0}','{1}','{2}','{3}','{4}','{5}','{6}')".format(New_CID, New_M_CName, New_M_Email, New_M_PW, New_M_gender, New_M_PNum, New_M_address)
                cur.execute(Sql)
                conn.commit()
                message = 'Membership added successfully!'
        elif Function_ID == '2':
            Update_M_CID = request.form['Update_M_CID']
            Sql = "Select * From Customers Where C_ID = '{0}'".format(Update_M_CID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                myresult_list = list(myresult)
                Update_M_CName = request.form['Update_M_CName']
                Update_M_Email = request.form['Update_M_Email']
                Update_M_PW = request.form['Update_M_PW']
                Update_M_gender = request.form['Update_M_gender']
                Update_M_PNum = request.form['Update_M_PNum']
                Update_M_address = request.form['Update_M_address']
                Update_M_Points = request.form['Update_M_Points']
                if Update_M_CName != '':
                    myresult_list[1] = Update_M_CName
                if Update_M_Email != '':
                    myresult_list[2] = Update_M_Email
                if Update_M_PW != '':
                    myresult_list[3] = Update_M_PW
                if Update_M_gender != '':
                    myresult_list[4] = Update_M_gender
                if Update_M_PNum != '':
                    myresult_list[5] = Update_M_PNum
                if Update_M_address != '':
                    myresult_list[6] = Update_M_address
                if Update_M_Points != '':
                    myresult_list[7] = Update_M_Points
                Sql = "Update Customers Set C_Name = '{0}', C_Email = '{1}', C_Password = '{2}', gender = '{3}', Phone_Num = '{4}', Address = '{5}', M_Point = '{6}'  Where C_ID = '{7}'".format(myresult_list[1],myresult_list[2],myresult_list[3],myresult_list[4],myresult_list[5],myresult_list[6],myresult_list[7],Update_M_CID)
                cur.execute(Sql)
                conn.commit()
                Update_message = 'Customer Info Update successfully!'
            else:
                Update_message = 'Unable to find customer, please enter again!'
        elif Function_ID == '3':
            D_CID = request.form['D_CID']
            Sql = "Select * From Customers Where C_ID = '{0}'".format(D_CID)
            cur.execute(Sql)
            myresult = cur.fetchone()
            if myresult:
                Sql = "Delete From Customers Where C_ID = '{0}'".format(D_CID)
                cur.execute(Sql)
                conn.commit()
                Delete_message = 'Record deleted successfully!'
            else:
                Delete_message = 'Unable to find the customer, please enter again!'
    Sql = "Select C_ID, C_Name, C_Email, gender, Phone_Num, Address, M_Point From Customers"
    cur.execute(Sql)
    Customer_Table = []
    for row in cur:
        Customer_Table.append(row)
    Customer_Table = tabulate(Customer_Table, tablefmt='html')
    return render_template('Membership.html', Customer_Table = Customer_Table, message = message, Update_message = Update_message, Delete_message = Delete_message, User_Name = User_Name)

@app.route('/Logout')
def Logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
