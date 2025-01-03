from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import stripe
import os
from dotenv import load_dotenv
from waitress import serve
load_dotenv()



app = Flask(__name__)
app.config['SECRET_KEY'] = 'yetgryhutjklkhjghfgdfsegrhytjkylkjythrgefarhtj'  
app.config['SESSION_TYPE'] = 'filesystem'


stripe.api_key = os.getenv("STRIPE_PRIVATE")  
webhook_secret = os.getenv("STRIPE_WEBHOOK")  

PRODUCTS = {
    'ubuntu': {
        'name': 'Ubuntu Edition',
        'base_price': 2000,
        'price_id': 'your_stripe_price_id_for_ubuntu'
    },
    'pop_os': {
        'name': 'Pop!_OS Edition',
        'base_price': 3000,
        'price_id': 'your_stripe_price_id_for_pop_os'
    },
    'arch': {
        'name': 'Arch Linux Edition',
        'base_price': 4000,
        'price_id': 'your_stripe_price_id_for_arch'
    },
    'mint': {
        'name': 'Linux Mint Edition',
        'base_price': 2500,
        'price_id': 'your_stripe_price_id_for_mint'
    }
}

STORAGE_PRICES = {
    '32': 500,    
    '64': 1000,   
    '128': 1500,  
    '256': 2500,  
    '512': 4000,  
    '1024': 9000  
}

@app.route("/create-checkout-session", methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        product_id = data.get('product')
        storage_size = data.get('storage')
        
        if product_id not in PRODUCTS:
            return jsonify({'error': 'Invalid product'}), 400
            
        product = PRODUCTS[product_id]
        storage_price = STORAGE_PRICES.get(storage_size, 0)
        total_amount = product['base_price'] + storage_price

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': total_amount,
                    'product_data': {
                        'name': f"{product['name']} with {storage_size}GB Storage. Incudes the USB drive.",
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'pricing',
            metadata={
                'product_id': product_id,
                'storage_size': storage_size
            }
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        
        
        
        
        print(f"Payment successful for {session.metadata.product_id} with {session.metadata.storage_size}GB storage")

    return jsonify({'status': 'success'})

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/support")
def support():
    return render_template("legal.html")

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)