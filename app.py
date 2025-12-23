from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'finance.db')
print(f"Database path: {os.path.join(os.getcwd(), 'finance.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# 数据库模型定义
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    
    def __repr__(self):
        return f"用户('{self.username}', '{self.email}', '{self.role}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"商品('{self.name}', '{self.category}', '{self.price}')"

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f"供应商('{self.name}', '{self.contact}', '{self.phone}')"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('purchases', lazy=True))
    supplier = db.relationship('Supplier', backref=db.backref('purchases', lazy=True))
    
    def __repr__(self):
        return f"采购记录('{self.product.name}', '{self.quantity}', '{self.purchase_date}')"

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('sales', lazy=True))
    
    def __repr__(self):
        return f"销售记录('{self.product.name}', '{self.quantity}', '{self.sale_date}')"

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('inventory', lazy=True, uselist=False))
    
    def __repr__(self):
        return f"库存记录('{self.product.name}', '{self.quantity}', '{self.last_updated}')"

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    expense_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"费用记录('{self.description}', '{self.amount}', '{self.expense_date}')"

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    income_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"收入记录('{self.description}', '{self.amount}', '{self.income_date}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由定义
@app.route("/")
@app.route("/home")
@login_required
def home():
    from datetime import date
    
    # 计算统计数据
    product_count = Product.query.count()
    
    # 今日销售
    today = date.today()
    today_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(db.func.date(Sale.sale_date) == today).scalar() or 0
    
    # 本月销售和成本
    this_month = today.month
    this_year = today.year
    
    month_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        db.func.strftime('%m', Sale.sale_date) == f'{this_month:02d}',
        db.func.strftime('%Y', Sale.sale_date) == f'{this_year}'
    ).scalar() or 0
    
    month_purchases = db.session.query(db.func.sum(Purchase.total_cost)).filter(
        db.func.strftime('%m', Purchase.purchase_date) == f'{this_month:02d}',
        db.func.strftime('%Y', Purchase.purchase_date) == f'{this_year}'
    ).scalar() or 0
    
    month_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        db.func.strftime('%m', Expense.expense_date) == f'{this_month:02d}',
        db.func.strftime('%Y', Expense.expense_date) == f'{this_year}'
    ).scalar() or 0
    
    month_profit = month_sales - month_purchases - month_expenses
    
    # 低库存商品（库存小于10的商品）
    low_stock_count = db.session.query(db.func.count(Inventory.id)).filter(Inventory.quantity < 10).scalar() or 0
    
    return render_template('home.html', 
                           product_count=product_count,
                           today_sales=round(today_sales, 2),
                           month_profit=round(month_profit, 2),
                           low_stock_count=low_stock_count)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('该邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('登录失败，请检查邮箱和密码', 'danger')
    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

# 商品管理路由
@app.route("/products")
@login_required
def product_list():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route("/product/add", methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        cost_price = float(request.form['cost_price'])
        
        # 检查商品是否已存在
        existing_product = Product.query.filter_by(name=name).first()
        if existing_product:
            flash('该商品已存在', 'danger')
            return redirect(url_for('add_product'))
        
        product = Product(name=name, category=category, price=price, cost_price=cost_price)
        db.session.add(product)
        db.session.commit()
        
        # 初始化库存
        inventory = Inventory(product_id=product.id, quantity=0)
        db.session.add(inventory)
        db.session.commit()
        
        flash('商品添加成功', 'success')
        return redirect(url_for('product_list'))
    return render_template('add_product.html')

@app.route("/product/<int:product_id>/update", methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.category = request.form['category']
        product.price = float(request.form['price'])
        product.cost_price = float(request.form['cost_price'])
        db.session.commit()
        flash('商品信息更新成功', 'success')
        return redirect(url_for('product_list'))
    return render_template('update_product.html', product=product)

@app.route("/product/<int:product_id>/delete", methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('商品已删除', 'success')
    return redirect(url_for('product_list'))

# 供应商管理路由
@app.route("/suppliers")
@login_required
def supplier_list():
    suppliers = Supplier.query.all()
    return render_template('supplier_list.html', suppliers=suppliers)

@app.route("/supplier/add", methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        phone = request.form['phone']
        address = request.form['address']
        
        # 检查供应商是否已存在
        existing_supplier = Supplier.query.filter_by(name=name).first()
        if existing_supplier:
            flash('该供应商已存在', 'danger')
            return redirect(url_for('add_supplier'))
        
        supplier = Supplier(name=name, contact=contact, phone=phone, address=address)
        db.session.add(supplier)
        db.session.commit()
        
        flash('供应商添加成功', 'success')
        return redirect(url_for('supplier_list'))
    return render_template('add_supplier.html')

@app.route("/supplier/<int:supplier_id>/update", methods=['GET', 'POST'])
@login_required
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if request.method == 'POST':
        supplier.name = request.form['name']
        supplier.contact = request.form['contact']
        supplier.phone = request.form['phone']
        supplier.address = request.form['address']
        db.session.commit()
        flash('供应商信息更新成功', 'success')
        return redirect(url_for('supplier_list'))
    return render_template('update_supplier.html', supplier=supplier)

@app.route("/supplier/<int:supplier_id>/delete", methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    flash('供应商已删除', 'success')
    return redirect(url_for('supplier_list'))

# 采购管理路由
@app.route("/purchases")
@login_required
def purchase_list():
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()
    return render_template('purchase_list.html', purchases=purchases)

@app.route("/purchase/add", methods=['GET', 'POST'])
@login_required
def add_purchase():
    products = Product.query.all()
    suppliers = Supplier.query.all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        supplier_id = int(request.form['supplier_id'])
        quantity = int(request.form['quantity'])
        
        # 获取商品信息
        product = Product.query.get_or_404(product_id)
        total_cost = product.cost_price * quantity
        
        # 创建采购记录
        purchase = Purchase(product_id=product_id, supplier_id=supplier_id, quantity=quantity, total_cost=total_cost)
        db.session.add(purchase)
        
        # 更新库存
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if inventory:
            inventory.quantity += quantity
            inventory.last_updated = datetime.utcnow()
        else:
            inventory = Inventory(product_id=product_id, quantity=quantity)
            db.session.add(inventory)
        
        db.session.commit()
        flash('采购记录添加成功', 'success')
        return redirect(url_for('purchase_list'))
    return render_template('add_purchase.html', products=products, suppliers=suppliers)

@app.route("/purchase/<int:purchase_id>/delete", methods=['POST'])
@login_required
def delete_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    
    # 更新库存（撤销采购）
    inventory = Inventory.query.filter_by(product_id=purchase.product_id).first()
    if inventory and inventory.quantity >= purchase.quantity:
        inventory.quantity -= purchase.quantity
        inventory.last_updated = datetime.utcnow()
    
    db.session.delete(purchase)
    db.session.commit()
    flash('采购记录已删除', 'success')
    return redirect(url_for('purchase_list'))

# 销售管理路由
@app.route("/sales")
@login_required
def sale_list():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sale_list.html', sales=sales)

@app.route("/sale/add", methods=['GET', 'POST'])
@login_required
def add_sale():
    products = Product.query.all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        
        # 获取商品信息
        product = Product.query.get_or_404(product_id)
        
        # 检查库存
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory or inventory.quantity < quantity:
            flash('库存不足，无法完成销售', 'danger')
            return redirect(url_for('add_sale'))
        
        # 计算总金额
        total_amount = product.price * quantity
        
        # 创建销售记录
        sale = Sale(product_id=product_id, quantity=quantity, total_amount=total_amount)
        db.session.add(sale)
        
        # 更新库存
        inventory.quantity -= quantity
        inventory.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash('销售记录添加成功', 'success')
        return redirect(url_for('sale_list'))
    return render_template('add_sale.html', products=products)

@app.route("/sale/<int:sale_id>/delete", methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    # 更新库存（撤销销售）
    inventory = Inventory.query.filter_by(product_id=sale.product_id).first()
    if inventory:
        inventory.quantity += sale.quantity
        inventory.last_updated = datetime.utcnow()
    
    db.session.delete(sale)
    db.session.commit()
    flash('销售记录已删除', 'success')
    return redirect(url_for('sale_list'))

# 财务管理路由
@app.route("/expenses")
@login_required
def expense_list():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return render_template('expense_list.html', expenses=expenses)

@app.route("/expense/add", methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        
        expense = Expense(description=description, amount=amount, category=category)
        db.session.add(expense)
        db.session.commit()
        
        flash('费用记录添加成功', 'success')
        return redirect(url_for('expense_list'))
    return render_template('add_expense.html')

@app.route("/expense/<int:expense_id>/delete", methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('费用记录已删除', 'success')
    return redirect(url_for('expense_list'))

@app.route("/incomes")
@login_required
def income_list():
    incomes = Income.query.order_by(Income.income_date.desc()).all()
    return render_template('income_list.html', incomes=incomes)

@app.route("/income/add", methods=['GET', 'POST'])
@login_required
def add_income():
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        
        income = Income(description=description, amount=amount, category=category)
        db.session.add(income)
        db.session.commit()
        
        flash('收入记录添加成功', 'success')
        return redirect(url_for('income_list'))
    return render_template('add_income.html')

@app.route("/income/<int:income_id>/delete", methods=['POST'])
@login_required
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    db.session.delete(income)
    db.session.commit()
    flash('收入记录已删除', 'success')
    return redirect(url_for('income_list'))

# 报表分析路由
@app.route("/report/sales")
@login_required
def sales_report():
    from datetime import date, timedelta
    
    # 获取最近30天的销售数据
    today = date.today()
    start_date = today - timedelta(days=29)
    
    # 按日期分组统计销售额
    daily_sales = db.session.query(
        db.func.date(Sale.sale_date).label('sale_date'),
        db.func.sum(Sale.total_amount).label('total_amount')
    ).filter(
        db.func.date(Sale.sale_date) >= start_date
    ).group_by(
        db.func.date(Sale.sale_date)
    ).order_by(
        db.func.date(Sale.sale_date)
    ).all()
    
    # 按月分组统计销售额
    monthly_sales = db.session.query(
        db.func.strftime('%Y-%m', Sale.sale_date).label('month'),
        db.func.sum(Sale.total_amount).label('total_amount')
    ).group_by(
        db.func.strftime('%Y-%m', Sale.sale_date)
    ).order_by(
        'month'
    ).all()
    
    # 按商品分组统计销售额
    product_sales = db.session.query(
        Product.name,
        db.func.sum(Sale.quantity).label('total_quantity'),
        db.func.sum(Sale.total_amount).label('total_amount')
    ).join(
        Sale
    ).group_by(
        Product.name
    ).order_by(
        db.desc('total_amount')
    ).limit(10).all()
    
    return render_template('sales_report.html', 
                           daily_sales=daily_sales,
                           monthly_sales=monthly_sales,
                           product_sales=product_sales)

@app.route("/report/inventory")
@login_required
def inventory_report():
    # 获取所有商品的库存信息
    inventory_items = db.session.query(
        Product.name,
        Product.category,
        Inventory.quantity,
        Product.price
    ).join(
        Inventory
    ).order_by(
        Inventory.quantity
    ).all()
    
    # 计算总库存价值
    total_inventory_value = db.session.query(
        db.func.sum(Product.price * Inventory.quantity)
    ).join(
        Inventory
    ).scalar() or 0
    
    # 按类别统计库存
    category_inventory = db.session.query(
        Product.category,
        db.func.sum(Inventory.quantity).label('total_quantity'),
        db.func.sum(Product.price * Inventory.quantity).label('total_value')
    ).join(
        Inventory
    ).group_by(
        Product.category
    ).order_by(
        'category'
    ).all()
    
    # 低库存商品（库存小于10）
    low_stock_items = db.session.query(
        Product.name,
        Product.category,
        Inventory.quantity
    ).join(
        Inventory
    ).filter(
        Inventory.quantity < 10
    ).order_by(
        Inventory.quantity
    ).all()
    
    return render_template('inventory_report.html',
                          inventory_items=inventory_items,
                          total_inventory_value=total_inventory_value,
                          category_inventory=category_inventory,
                          low_stock_items=low_stock_items)

@app.route("/report/financial")
@login_required
def financial_report():
    from datetime import date
    
    today = date.today()
    
    # 本月财务数据
    month_start = date(today.year, today.month, 1)
    
    # 本月销售额
    month_sales = db.session.query(
        db.func.sum(Sale.total_amount)
    ).filter(
        Sale.sale_date >= month_start
    ).scalar() or 0
    
    # 本月采购成本
    month_purchase_cost = db.session.query(
        db.func.sum(Purchase.total_cost)
    ).filter(
        Purchase.purchase_date >= month_start
    ).scalar() or 0
    
    # 本月费用
    month_expenses = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        Expense.expense_date >= month_start
    ).scalar() or 0
    
    # 本月收入（包括销售和其他收入）
    month_other_income = db.session.query(
        db.func.sum(Income.amount)
    ).filter(
        Income.income_date >= month_start
    ).scalar() or 0
    
    # 计算本月利润
    month_profit = (month_sales + month_other_income) - (month_purchase_cost + month_expenses)
    
    # 费用分类统计
    expense_categories = db.session.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total_amount')
    ).filter(
        Expense.expense_date >= month_start
    ).group_by(
        Expense.category
    ).order_by(
        db.desc('total_amount')
    ).all()
    
    # 收入分类统计
    income_categories = db.session.query(
        Income.category,
        db.func.sum(Income.amount).label('total_amount')
    ).filter(
        Income.income_date >= month_start
    ).group_by(
        Income.category
    ).order_by(
        db.desc('total_amount')
    ).all()
    
    # 资产负债表数据
    # 库存价值（按成本价计算）
    total_inventory_value = db.session.query(
        db.func.sum(Product.cost_price * Inventory.quantity)
    ).join(
        Inventory, Product.id == Inventory.product_id
    ).scalar() or 0
    
    # 计算总资产（库存价值 + 本月利润）
    total_assets = total_inventory_value + month_profit
    
    # 简化的负债和所有者权益计算
    # 假设利润全部计入所有者权益
    total_equity = month_profit
    total_liabilities = 0  # 暂时没有负债数据
    
    # 现金流量表数据
    # 经营活动现金流入
    operating_cash_in = month_sales + month_other_income
    
    # 经营活动现金流出
    operating_cash_out = month_purchase_cost + month_expenses
    
    # 净现金流量
    net_cash_flow = operating_cash_in - operating_cash_out
    
    return render_template('financial_report.html',
                          month_sales=month_sales,
                          month_purchase_cost=month_purchase_cost,
                          month_expenses=month_expenses,
                          month_other_income=month_other_income,
                          month_profit=month_profit,
                          expense_categories=expense_categories,
                          income_categories=income_categories,
                          total_inventory_value=total_inventory_value,
                          total_assets=total_assets,
                          total_liabilities=total_liabilities,
                          total_equity=total_equity,
                          operating_cash_in=operating_cash_in,
                          operating_cash_out=operating_cash_out,
                          net_cash_flow=net_cash_flow)

# 创建数据库
def create_db():
    with app.app_context():
        db.create_all()
        # 创建默认管理员用户
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(username='admin', email='admin@example.com', password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()

if __name__ == '__main__':
    create_db()
    app.run(debug=True)