from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Configuração da aplicação
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

# Inicializando a base de dados
db = SQLAlchemy(app)

#------------------------------------------------------------------------------Tabelas-----------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)  # Armazenamento com hash

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)  # Vincular ao médico
    appointment_date = db.Column(db.Date, nullable=False, unique=True)

class DoctorRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Avaliação por um usuário
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(500), nullable=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    specialty = db.Column(db.String(50), nullable=False)
    photo = db.Column(db.String(100), nullable=False)  # Caminho da imagem do médico

with app.app_context():
    db.create_all()

#------------------------------------------------------------------------------ROTAS(URL)-----------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verifica se o usuário existe no banco
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            return redirect(url_for('menu'))
        else:
            return 'Credenciais inválidas. Tente novamente.'
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Captura os dados do formulário
        username = request.form.get('username')
        password = request.form.get('password')

        # Verifica se o usuário já existe no banco
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Usuário já existe. Faça login.'

        # Cria um novo usuário
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Redireciona para a página de login
        return redirect(url_for('login'))
    
    # Exibe o formulário de registro se o método for GET
    return render_template('register.html')

@app.route('/logout')
def logout():
    # Remove o user_id da sessão
    session.pop('user_id', None)
    flash("Você saiu da conta com sucesso.", 'success')
    return redirect(url_for('login'))

@app.route('/menu')
def menu():
    return render_template('menu.html')









@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'POST':
        selected_date = request.form['appointment_date']
        parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Verificar se a data já foi escolhida por outro usuário
        existing_appointment = Appointment.query.filter_by(appointment_date=parsed_date).first()
        if existing_appointment:
            flash('Essa data já foi agendada, por favor selecione outra data.', 'error')
            return redirect(url_for('schedule'))

        # Agendar a consulta
        new_appointment = Appointment(user_id=1, appointment_date=parsed_date)  # user_id é 1 só como exemplo
        db.session.add(new_appointment)
        db.session.commit()
        flash('Consulta agendada com sucesso!', 'success')
        return redirect(url_for('schedule'))

    return render_template('schedule.html')

# Rota para a página de seleção de médicos
@app.route('/select-doctor', methods=['GET', 'POST'])
def select_doctor():
    if request.method == 'POST':
        specialty = request.form['specialty']
        selected_doctor = Doctor.query.filter_by(specialty=specialty).first()
        if selected_doctor:
            return render_template('select_doctor.html', selected_doctor=selected_doctor)
        else:
            flash('Nenhum médico disponível para esta especialidade.', 'error')
    return render_template('select_doctor.html')

# Rota para agendar com o médico selecionado
@app.route('/schedule_appointment/<int:doctor_id>', methods=['GET'])
def schedule_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    flash(f'Você agendou uma consulta com o Dr. {doctor.name}.', 'success')
    return redirect(url_for('select_doctor'))
    


@app.route('/rate-doctor/<int:doctor_id>', methods=['GET', 'POST'])
def rate_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    if request.method == 'POST':
        rating = int(request.form['rating'])
        review = request.form.get('review', '')

        # Armazenar a avaliação no banco de dados
        new_rating = DoctorRating(doctor_id=doctor_id, rating=rating, review=review)
        db.session.add(new_rating)
        db.session.commit()

        flash('Avaliação enviada com sucesso!', 'success')
        return redirect(url_for('rate_doctor', doctor_id=doctor_id))

    return render_template('rate_doctor.html', doctor_id=doctor_id, doctor=doctor)


@app.route('/list_data')
def list_data():
    # Consultar todos os usuários
    users = User.query.all()
    
    # Consultar todas as consultas agendadas
    appointments = Appointment.query.all()
    
    # Consultar todos os médicos
    doctors = Doctor.query.all()
    
    # Consultar todas as avaliações de médicos
    ratings = DoctorRating.query.all()
    
    # Criando uma string para exibir os dados no HTML
    result = "<h1>Lista de Dados</h1>"
    
    # Listar Usuários
    result += "<h2>Usuários</h2>"
    for user in users:
        result += f"ID: {user.id}, Usuário: {user.username}<br>"
    
    # Listar Consultas Agendadas
    result += "<h2>Consultas Agendadas</h2>"
    for appointment in appointments:
        result += f"ID: {appointment.id}, Paciente: {appointment.user_id}, Médico: , Data: {appointment.appointment_date} <br>"
    
    # Listar Médicos
    result += "<h2>Médicos</h2>"
    for doctor in doctors:
        result += f"ID: {doctor.id}, Nome: {doctor.name}, Especialidade: {doctor.specialty}<br>"
    
    # Listar Avaliações de Médicos
    result += "<h2>Avaliações de Médicos</h2>"
    for rating in ratings:
        result += f"ID: {rating.id}, Médico: {rating.doctor_id}, Paciente: , Nota: {rating.rating}, Comentário: {rating.review}<br>"
    
    return result




@app.route('/list_users')
def list_users():
    # Consultando todos os usuários cadastrados
    users = User.query.all()

    # Criando uma string para exibir os resultados
    user_list = ""
    for user in users:
        user_list += f"ID: {user.id}, Usuário: {user.username}, Senha: {user.password}<br>"

    return user_list











if __name__ == '__main__':
    app.run(debug=True)


# Populando a tabela Doctor
def populate_doctors():
    doctors = [
        Doctor(name='Dr. Carlos Silva', specialty='Cardiologista', photo='https://static.vecteezy.com/system/resources/previews/036/094/750/non_2x/ai-generated-senior-doctor-black-man-arms-crossed-with-smile-pride-on-transparent-background-free-png.png'),
        Doctor(name='Dr. Pedro Almeida', specialty='Pediatra', photo='https://snapheadshots.com/_ipx/f_webp/images/headshot-types/doctor/feat_1.png'),
        Doctor(name='Dr. Renato Oliveira', specialty='Clínico Geral', photo='https://static.vecteezy.com/system/resources/previews/036/094/521/non_2x/ai-generated-senior-doctor-asia-man-arms-crossed-with-smile-pride-on-transparent-background-free-png.png'),
    ]

    db.session.add_all(doctors)
    db.session.commit()
    print("Tabela doctor populada com sucesso!")

# Chamando a função para popular a tabela
with app.app_context():
    populate_doctors()