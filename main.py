from fastapi import FastAPI

# Create a FastAPI instance
app = FastAPI()

# Define a root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

# Initialize FastAPI
app = FastAPI()

# OpenAI API key setup
openai.api_key = 'API_KEY'

# In-memory database for lenders
lenders_db = {
    "lender_a": {"loan_amount": 500000, "interest_rate": 6.5, "credit_score": 700, "location": "urban"},
    "lender_b": {"loan_amount": 400000, "interest_rate": 5.0, "credit_score": 720, "location": "urban"},
    "lender_c": {"loan_amount": 300000, "interest_rate": 4.5, "credit_score": 680, "location": "rural"},
    "lender_d": {"loan_amount": 200000, "interest_rate": 3.5, "credit_score": 700, "location": "urban"},
    "lender_e": {"loan_amount": 700000, "interest_rate": 5.5, "credit_score": 690, "location": "urban"},
    "lender_f": {"loan_amount": 500000, "interest_rate": 1.5, "credit_score": 720, "location": "rural"},
    "lender_g": {"loan_amount": 900000, "interest_rate": 3.5, "credit_score": 650, "location": "rural"},
    "lender_h": {"loan_amount": 600000, "interest_rate": 4.5, "credit_score": 670, "location": "urban"},
}

# Borrower request model
class BorrowerRequest(BaseModel):
    message: str

# Function to match lenders in the database based on user input
def match_lenders(loan_amount: float, credit_score: int, location: str):
    matched_lenders = []
    for lender_id, lender_data in lenders_db.items():
        if (lender_data["loan_amount"] >= loan_amount and
            lender_data["credit_score"] <= credit_score and
            lender_data["location"] == location):
            matched_lenders.append({
                "lender": lender_id,
                "interest_rate": lender_data["interest_rate"],
                "loan_amount": lender_data["loan_amount"]
            })
    return matched_lenders


# Function to generate text using OpenAI's chat completion API
def generate_openai_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-0613", 
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Chatbot endpoint to handle user requests
@app.post("/generate_text/")
def generate_text(request: BorrowerRequest):
    user_message = request.message.lower()

    # Check if the message includes loan-related information for lender matching
    if "loan" in user_message and "credit score" in user_message and ("urban" in user_message or "rural" in user_message):
        
        try:
            # Extract loan amount
            loan_amount = float(next(word for word in user_message.split() if word.replace(',', '').replace('.', '').isdigit()))

            # Extract credit score
            credit_score = int(next(word for word in user_message.split() if word.isdigit() and len(word) == 3))

            # Extract location (either urban or rural)
            location = "urban" if "urban" in user_message else "rural"

            # Match lenders based on extracted information
            matched_lenders = match_lenders(loan_amount, credit_score, location)

            # Return matched lenders to the user
            if matched_lenders:
                lender_info = "\n".join([f"{lender['lender']}: Loan amount of ${lender['loan_amount']} at {lender['interest_rate']}% interest rate" for lender in matched_lenders])
                return {"response": f"I found the following lenders for your request:\n\n{lender_info}"}
            else:
                return {"response": "Sorry, I couldn't find any lenders matching your criteria. You might want to adjust your loan amount, credit score, or location."}

        except (ValueError, StopIteration):
            return {"response": "It looks like I couldn't understand your loan amount or credit score. Could you please provide them clearly?"}
    
    # If no specific loan-related information is provided, handle general queries
    else:
        # Pass the user's message to OpenAI for general text generation
        try:
            response = generate_openai_response(user_message)
            return {"response": response}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

