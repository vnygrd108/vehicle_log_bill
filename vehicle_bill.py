from flask import Flask, request, render_template, send_file
import pandas as pd
import math
from datetime import datetime
import os

app = Flask(__name__)

# Vehicle rates
rates = {
    'tata407': 25,
    'dzire': 16,
    'bolero_pickup': 18,
    'ertiga_mh43_cc3406': 16
}

def calculate_bill(row):
    vehicle = row['vehicle']
    rate = rates.get(vehicle, 0)

    trip_kms = row.get('Trip Kms', 0) or 0
    toll_tax = row.get('Toll Tax', 0) or 0
    waiting_time = row.get('Waiting_Time', 0) or 0
    trip_duration = row.get('Trip Duration', 0) or 0

    base_charge = trip_kms * rate
    waiting_charge = waiting_time * 100
    overtime_hours = max(trip_duration - 9, 0)
    overtime_charge = overtime_hours * 100

    total_charge = base_charge + toll_tax + waiting_charge + overtime_charge
    rounded_total = math.ceil(total_charge / 100) * 100
    return rounded_total

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        try:
            start_date = pd.to_datetime(start_date_str)
            end_date = pd.to_datetime(end_date_str)
        except Exception as e:
            return f"Invalid dates: {e}"

        # Read Excel
        excel_file_path = 'Vehicle_Log_Data_22-24.xlsx'
        df = pd.read_excel(excel_file_path, sheet_name='data')

        df.drop(columns=['Bill Amount'], inplace=True, errors='ignore')
        df['Trip Start'] = pd.to_datetime(df['Trip Start'], errors='coerce')
        df['Trip End'] = pd.to_datetime(df['Trip End'], errors='coerce')

        # Filter date range
        df = df[(df['Trip Start'] >= start_date) & (df['Trip Start'] <= end_date)]

        # Convert to numeric
        numeric_cols = ['Trip Kms', 'Toll Tax', 'Waiting_Time', 'Trip Duration']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Calculate bills
        df['Calculated Bill'] = df.apply(calculate_bill, axis=1)
        df['Trip Duration'] = pd.to_numeric(df['Trip Duration'], errors='coerce')
        df['Overtime'] = df['Trip Duration'].apply(lambda x: max(x - 9, 0))

        df = df[['Bill_Entity', 'Driver', 'Dept', 'Service_Hired', 'vehicle', 'Requestor', 'User', 'Destination',
                 'Trip Start', 'Trip End', 'Start Dial', 'End Dial', 'Trip Kms', 'Toll Tax',
                 'Fuel Expense', 'Waiting_Time', 'Driver_Time', 'Trip Duration', 'Calculated Bill']]

        # Format date columns
        df['Trip Start'] = pd.to_datetime(df['Trip Start'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
        df['Trip End'] = pd.to_datetime(df['Trip End'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
        df = df.sort_values(by='Trip Start', ascending=True)

        # Export to Excel
        file_name = f"vehicle_log_bills_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}.xlsx"
        file_path = os.path.join('output', file_name)
        os.makedirs('output', exist_ok=True)
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
