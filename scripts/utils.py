import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker for generating fake data with a South African locale
fake = Faker('zu_ZA')

# --- Data Structures for Demographics ---
SA_NAMES = {
    "Black": [
        {"name": "Thabo", "gender": "male"}, {"name": "Ayanda", "gender": "female"}, {"name": "Ayanda", "gender": "male"}, {"name": "Kagiso", "gender": "male"},
        {"name": "Kagiso", "gender": "female"}, {"name": "Lerato", "gender": "female"}, {"name": "Sibusiso", "gender": "male"}, {"name": "Nomvula", "gender": "female"},
        {"name": "Sipho", "gender": "male"}, {"name": "Nokuthula", "gender": "female"}, {"name": "Mpho", "gender": "female"}, {"name": "Tumelo", "gender": "male"},
        {"name": "Thandi", "gender": "female"}, {"name": "Simphiwe", "gender": "female"}, {"name": "Siphiwe", "gender": "male"}, {"name": "Andile", "gender": "male"},
        {"name": "Zandile", "gender": "female"}, {"name": "Zanele", "gender": "female"}, {"name": "Karabo", "gender": "unisex"}, {"name": "Tebogo", "gender": "male"},
        {"name": "Naledi", "gender": "female"}, {"name": "Palesa", "gender": "female"}, {"name": "Boitumelo", "gender": "female"}, {"name": "Lehlohonolo", "gender": "male"},
        {"name": "Bongani", "gender": "male"}, {"name": "Nokwazi", "gender": "female"}, {"name": "Tshepo", "gender": "male"}, {"name": "Nandi", "gender": "female"},
        {"name": "Lwazi", "gender": "male"}, {"name": "Gugu", "gender": "female"}, {"name": "Vusi", "gender": "male"}, {"name": "Nosipho", "gender": "female"},
        {"name": "Khanyisile", "gender": "female"}, {"name": "Mncedisi", "gender": "male"}, {"name": "Hlengiwe", "gender": "female"}, {"name": "Mduduzi", "gender": "male"},
        {"name": "Noluthando", "gender": "female"}, {"name": "Themba", "gender": "male"}, {"name": "Zodwa", "gender": "female"}, {"name": "Mxolisi", "gender": "male"},
        {"name": "Busisiwe", "gender": "female"}, {"name": "Phumlani", "gender": "male"}, {"name": "Nomsa", "gender": "female"}, {"name": "Bheki", "gender": "male"},
        {"name": "Makhosi", "gender": "female"}, {"name": "Sandile", "gender": "male"}, {"name": "Njabulo", "gender": "male"},
        {"name": "Thulisile", "gender": "female"}, {"name": "Khulekani", "gender": "male"}, {"name": "Sibongile", "gender": "female"}, {"name": "Mzwandile", "gender": "male"},
        {"name": "Nomthandazo", "gender": "female"}, {"name": "Xolani", "gender": "male"},{'name': 'Andisiwe', 'gender': 'female'}, {'name': 'Anele', 'gender': 'female'}, 
        {'name': 'Asanda', 'gender': 'female'}, {'name': 'Ayo', 'gender': 'female'}, {'name': 'Busi', 'gender': 'female'}, {'name': 'Dineo', 'gender': 'female'},
        {'name': 'Esihle', 'gender': 'female'}, {'name': 'Lesedi', 'gender': 'female'}, {'name': 'Lindokuhle', 'gender': 'female'},
        {'name': 'Iminathi', 'gender': 'female'}, {'name': 'Mandisa', 'gender': 'female'}, {'name': 'Jabulile', 'gender': 'female'},{'name': 'Mmapula', 'gender': 'female'},
        {'name': 'Kaya', 'gender': 'female'},{'name': 'Naledi', 'gender': 'female'}, {'name': 'Kanyisa', 'gender': 'female'},{'name': 'Nandi', 'gender': 'female'},
        {'name': 'Keabetswe', 'gender': 'female'},{'name': 'Nokuthula', 'gender': 'female'}, {'name': 'Khethiwe', 'gender': 'female'},
        {'name': 'Nomsa', 'gender': 'female'},{'name': 'Nozipho', 'gender': 'female'}, {'name': 'Palesa', 'gender': 'female'},{'name': 'Zandi', 'gender': 'female'},
        {'name': 'Phumzile', 'gender': 'female'},{'name': 'Zandile', 'gender': 'female'}, {'name': 'Siphelele', 'gender': 'female'},{'name': 'Zinzi', 'gender': 'female'},
        {'name': 'Nokuzola', 'gender': 'female'},{'name': 'Amani', 'gender': 'male'}, {'name': 'Siphesihle', 'gender': 'female'},{'name': 'Amogelang', 'gender': 'male'},
        {'name': 'Siphokazi', 'gender': 'female'},{'name': 'Andile', 'gender': 'male'}, {'name': 'Ditebogo', 'gender': 'female'},{'name': 'Bandile', 'gender': 'male'},
        {'name': 'Thandiwe', 'gender': 'female'},{'name': 'Bongani', 'gender': 'male'}, {'name': 'Thobeka', 'gender': 'female'},{'name': 'Dali', 'gender': 'male'},
        {'name': 'Thuli', 'gender': 'female'},{'name': 'Neo', 'gender': 'male'}, {'name': 'Tshepiso', 'gender': 'female'},{'name': 'Fikile', 'gender': 'male'},
        {'name': 'Unathi', 'gender': 'female'},{'name': 'Hlengiwe', 'gender': 'male'}, {'name': 'Noxolo', 'gender': 'female'},{'name': 'Jabulani', 'gender': 'male'},
        {'name': 'Kabelo', 'gender': 'male'},{'name': 'Kagiso', 'gender': 'male'}, {'name': 'Kamva', 'gender': 'male'},{'name': 'Kgosi', 'gender': 'male'},
        {'name': 'Kgotso', 'gender': 'male'},{'name': 'Lerato', 'gender': 'male'}, {'name': 'Lindani', 'gender': 'male'},{'name': 'Loyiso', 'gender': 'male'},
        {'name': 'Lubanzi', 'gender': 'male'},{'name': 'Lwazi', 'gender': 'male'}, {'name': 'Mandla', 'gender': 'male'},{'name': 'Mphahlele', 'gender': 'male'},
        {'name': 'Mpho', 'gender': 'male'},{'name': 'Mthokozisi', 'gender': 'male'}, {'name': 'Nathi', 'gender': 'male'},
        {'name': 'Nkosinathi', 'gender': 'male'},{'name': 'Odirile', 'gender': 'male'}, {'name': 'Omphemetse', 'gender': 'male'},{'name': 'Phumlani', 'gender': 'male'},
        {'name': 'Sabelo', 'gender': 'male'},{'name': 'Sibusiso', 'gender': 'male'}, {'name': 'Siphamandla', 'gender': 'male'},{'name': 'Siphelele', 'gender': 'male'},
        {'name': 'Sipho', 'gender': 'male'},{'name': 'Thabiso', 'gender': 'male'}, {'name': 'Thabo', 'gender': 'male'},{'name': 'Thulani', 'gender': 'male'},
        {'name': 'Tshepo', 'gender': 'male'},{'name': 'Vusimuzi', 'gender': 'male'}, {'name': 'Xolani', 'gender': 'male'},
        {'name': 'Zola', 'gender': 'male'}
    ],
    "White": [
        {"name": "Johan", "gender": "male"}, {"name": "Annelie", "gender": "female"},
        {"name": "Pieter", "gender": "male"}, {"name": "Elmarie", "gender": "female"},
        {"name": "Jacques", "gender": "male"}, {"name": "Marike", "gender": "female"},
        {"name": "Hendrik", "gender": "male"}, {"name": "Carla", "gender": "female"},
        {"name": "Gerhard", "gender": "male"}, {"name": "Lize", "gender": "female"},
        {"name": "Francois", "gender": "male"}, {"name": "Marelize", "gender": "female"},
        {"name": "Stefan", "gender": "male"}, {"name": "Annette", "gender": "female"},
        {"name": "James", "gender": "male"}, {"name": "Janette", "gender": "female"},
        {"name": "Stephen", "gender": "male"}, {"name": "Stephanie", "gender": "female"},
        {"name": "Charl", "gender": "male"}, {"name": "Annetjie", "gender": "female"},
        {"name": "Janie", "gender": "male"}, {"name": "Janine", "gender": "female"},
        {"name": "Richard", "gender": "male"}, {"name": "Rochelle", "gender": "female"}
    ],
    "Coloured": [
        {"name": "Tyrone", "gender": "male"}, {"name": "Chantelle", "gender": "female"},
        {"name": "Denzel", "gender": "male"}, {"name": "Gail", "gender": "female"},
        {"name": "Shane", "gender": "male"}, {"name": "Monique", "gender": "female"},
        {"name": "Clint", "gender": "male"}, {"name": "Desiree", "gender": "female"},
        {"name": "Brandon", "gender": "male"}, {"name": "Candice", "gender": "female"},
        {'name': 'Amina', 'gender': 'female'},
        {"name": "Daylon", "gender": "male"}, {"name": "Danielle", "gender": "female"},
        {'name': 'Fatima', 'gender': 'female'}, {'name': 'Malika', 'gender': 'female'},
        {"name": "Jovan", "gender": "male"}, {"name": "Joelle", "gender": "female"},
        {"name": "Vinnie", "gender": "male"}, {"name": "Rochelle", "gender": "female"},
        {"name": "Clayton", "gender": "male"}, {"name": "Lizelle", "gender": "female"},
        {"name": "Kaylin", "gender": "male"}, {"name": "Kaylene", "gender": "female"},
        {"name": "Charlie", "gender": "male"},
        {"name": "Prinsley", "gender": "male"}, {"name": "Desire", "gender": "female"}
    ],
    "Indian": [
        {"name": "Yusuf", "gender": "male"}, {"name": "Aisha", "gender": "female"},
        {"name": "Rajesh", "gender": "male"}, {"name": "Priya", "gender": "female"},
        {"name": "Ahmed", "gender": "male"}, {"name": "Fatima", "gender": "female"},
        {"name": "Ismail", "gender": "male"}, {"name": "Zainab", "gender": "female"},
        {"name": "Kiran", "gender": "male"}, {"name": "Nadia", "gender": "female"},
        {"name": "Darman", "gender": "male"}, {"name": "Priyanka", "gender": "female"},
        {"name": "Surosh", "gender": "male"}, {"name": "Anusha", "gender": "female"},
        {"name": "Vinay", "gender": "male"}, {"name": "Vashti", "gender": "female"}
    ],
    'Foreign': [
        {'name': 'Simba', 'gender': 'male'}, {'name': 'Tinashe', 'gender': 'male'},{'name': 'John', 'gender': 'male'},
        {'name': 'Maria', 'gender': 'female'}, {'name': 'Ahmed', 'gender': 'male'},{'name': 'Chen', 'gender': 'male'},
        {'name': 'Fatima', 'gender': 'female'},{'name': 'David', 'gender': 'male'},{'name': 'Sofia', 'gender': 'female'},
        {'name': 'Ali', 'gender': 'male'},{'name': 'Linh', 'gender': 'female'},{'name': 'Ivan', 'gender': 'male'},
        {'name': 'Yakubu', 'gender': 'male'},{'name': 'Taiwo', 'gender': 'male'},{'name': 'Emeka', 'gender': 'male'},
        {'name': 'Halima', 'gender': 'female'},{'name': 'Ifeoma', 'gender': 'female'},{'name': 'Kehinde', 'gender': 'male'},
        {'name': 'Chinyere', 'gender': 'female'},{'name': 'Chioma', 'gender': 'female'},{'name': 'Wanjiru', 'gender': 'female'},
        {'name': 'Mwangi', 'gender': 'male'},{'name': 'Odhiambo', 'gender': 'male'},{'name': 'Ochieng', 'gender': 'male'},
        {'name': 'William', 'gender': 'male'},{'name': 'Amina', 'gender': 'female'},
        {'name': 'Onyango', 'gender': 'male'},{'name': 'Felo', 'gender': 'male'},{'name': 'Nneka', 'gender': 'female'},
        {'name': 'Abdullahi', 'gender': 'male'},{'name': 'Kemunto', 'gender': 'female'},{'name': 'Wambui', 'gender': 'female'},
        {'name': 'Wanjiku', 'gender': 'female'},{'name': 'Monica', 'gender': 'female'},{'name': 'Lawrence', 'gender': 'male'},
        {'name': 'Caleb', 'gender': 'male'},{'name': 'Denise', 'gender': 'female'},{'name': 'Dennis', 'gender': 'male'},
        {'name': 'Raphael', 'gender': 'male'}
    ]
}

SURNAMES_BY_RACE = {
    'Black': ['Shabalala', 'Mokoena', 'Dlamini', 'Ngcobo', 'Khumalo', 'Ndlovu', 'Zwane', 'Mthembu', 'Mabena', 'Mnguni',
              'Skosana', 'Ngwenya', 'Dube','Mothapo', 'Letsoalo', 'Kubeka', 'Sedumedi', 'Nteyi',
              'Motsepe', 'Radebe', 'Rabe', 'Zulu',"Nkosi", "Sithole", "Mahlangu",
              "Mkhize", "Gumede", "Buthelezi", "Khoza","Sibiya", "Mofokeng", "Mhlongo", "Baloyi", "Mbatha", "Mathebula",
              "Ntuli", "Mazibuko", "Tshabalala", "Nxumalo", "Chauke", "Cele", "Mthethwa", "Ngobeni", "Ngubane", "Maluleke", "Maseko",
              "Molefe", "Mtshali", "Mabaso", "Mkhwanazi", "Mnisi", "Zondi", "Moloi", "Mchunu", "Motaung", "Hlongwane", "Zungu", "Nkuna", "Hlatshwayo",
              "Shabangu", "Vilakazi", "Xaba", "Malatji", "Dladla", "Hadebe", "Majola", "Mohlala", "Kekana", "Kunene", "Xulu", "Khanyile",
              "Zuma", "Simelane", "Mudau", "Langa", "Nhlapo"],
    'White': ['Coetzee', 'Pretorius', 'Du Plessis', 'Van der Merwe', 'Joubert', 'Botha', 'Nel', 'Visser', 'Steyn', 'De Villiers',"van Wyk",
              "van Rooyen", "De Vos", "Viljoen", "van den Berg", "Kruger", "Du Toit", "Erasmus", "van Niekerk", "Meyer", "Booysen","Smith", "Williams",
              "Jacobs", "Adams",'Barnett'],
    'Coloured': ['Davids', 'Philander', 'Abrahams', 'Jacobs', 'Adams', 'October', 'Michaels', 'Solomons', 'Peters', 'Van Wyk',"Cloete",'Snyders'],
    'Indian': ['Naidoo', 'Pillay', 'Govender', 'Moodley', 'Singh', 'Reddy', 'Maharaj', 'Chetty', 'Padayachee', 'Rampersad','Moonsamy'],
    'Foreign': ['Smith', 'Hassan', 'Zhang', 'Nguyen', 'Ivanov', 'Fernandez', 'Almeida', 'Kim', 'Brown', 'Kowalski', 'Otieno', 'Mohamed',
                'Mwangi', 'Odhiambo', 'Maina', 'Ochieng', 'Ali', 'Onyango', 'Juma', 'Wambui', 'Njeri', 'Kariuki', 'Akinyi',
                'Achieng', 'Muthoni', 'Kimani', 'Adhiambo', 'Njuguna', 'Macharia', 'Barasa', 'Cheruiyot', 'Ibrahim', 'Musa',
                'Abubakar', 'Isah', 'Yakubu', 'Aminu', 'Yahaya', 'Shehu', 'Okafor', 'Okeke', 'Adebayo', 'Okoro', 'Okon', 'Chukwu',
                'Nwachukwu', 'Nwankwo', 'Okoye', 'Ogbonna', 'Adeyemi', 'Yunusa', 'Balogun', 'Nwafor', 'Effiong', 'Amadu', 'Sanusi',
                'Anyanwu', 'Danjuma', 'Ohakwu', 'Opara', 'Taiwo', 'Onuoha', 'Babatunde', 'Odemwingi','Yeboah']
}

GAUTENG_CITIES = [
    "Johannesburg", "Pretoria", "Ekurhuleni", "Soweto", "Vanderbijlpark",
    "Vereeniging", "Centurion", "Midrand", "Germiston", "Springs",
    "Benoni", "Boksburg", "Krugersdorp", "Randburg", "Roodepoort"
]

JOHANNESBURG_SUBURBS = sorted(list(set([
    "Auckland Park", "Braamfontein", "City and Suburban", "Doornfontein", "Fairland",
    "Fordsburg", "Greenside", "Houghton Estate", "Illovo", "Jeppestown",
    "Johannesburg Central", "Kensington", "Melville", "Newtown", "Norwood",
    "Observatory", "Parktown", "Rosebank", "Sandringham", "Sophiatown",
    "Troyeville", "Westdene", "Yeoville", "Alexandra", "Diepkloof",
    "Dobsonville", "Eldorado Park", "Greater Soweto", "Johannesburg South",
    "Lenasia", "Meadowlands", "Midrand", "Orange Farm", "Roodepoort",
    "Sandton", "Southgate", "Chartwell", "City of Johannesburg NU",
    "Dainfern", "Diepsloot", "Drie Ziek", "Ebony Park", "Ennerdale", "Farmall",
    "Itsoseng", "Ivory Park", "Kaalfontein", "Kagiso",
    "Kanana Park", "Lakeside", "Lanseria", "Lawley", "Lehae", "Lenasia South",
    "Lucky 7", "Malatjie", "Mayibuye", "Millgate Farm", "Poortjie", "Rabie Ridge",
    "Randfontein", "Rietfontein", "Stretford", "Tshepisong",
    "Vlakfontein", "Zakariyya Park", "Zevenfontein", "Beverley", "Bertrams",
    "Booysens", "Bruma", "Cresta", "Crown Mines", "Craighall Park", "Darrenwood",
    "Emmarentia", "Ferndale", "Glenhazel", "Highlands North", "Linden",
    "Lombardy East", "Malvern", "Mayfair", "Northcliff", "Parkhurst", "Rivonia",
    "Victory Park"
])))

# --- Helper Functions ---
def calculate_age(birthdate_str, today_str=None):
    """Calculates age from a birthdate string as of a given date. Handles errors gracefully."""
    if not isinstance(birthdate_str, str):
        return 0  # Return a default age if input is not a string
    try:
        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
        today = datetime.strptime(today_str, '%Y-%m-%d') if today_str else datetime.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except (ValueError, TypeError):
        return 0 # Return a default age if format is incorrect

def get_age_group(age):
    """Categorizes age into predefined groups."""
    if age <= 4:
        return "0-4"
    elif age <= 14:
        return "5-14"
    elif age <= 24:
        return "15-24"
    elif age <= 44:
        return "25-44"
    elif age <= 64:
        return "45-64"
    else: # age >= 65
        return "65+"

def generate_birthdate(min_age=0, max_age=100):
    """Generates a random birthdate string."""
    birth_year = datetime.today().year - random.randint(min_age, max_age)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28) # Use 28 to avoid month-day combination errors
    return datetime(birth_year, birth_month, birth_day).strftime('%Y-%m-%d')

def generate_gauteng_address():
    """Generates a random address within Gauteng."""
    city = random.choice(GAUTENG_CITIES)
    street_name = fake.street_name()
    street_number = random.randint(1, 200)
    return f"{street_number} {street_name}, {city}, Gauteng"

def classify_experience(years_of_service):
    """Classifies staff experience level based on years of service."""
    if years_of_service < 5:
        return "Junior"
    elif 5 <= years_of_service <= 15:
        return "Mid-Level"
    else:
        return "Senior"
