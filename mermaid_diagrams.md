# 超市财务管理系统Mermaid图表

## 1. 系统用例图

```mermaid
flowchart TD
    subgraph 系统用户
        User[用户]
        InventoryManager[库存管理员]
        SalesPerson[销售人员]
        FinancialStaff[财务人员]
        Manager[管理层]
    end
    
    subgraph 系统功能
        Login[用户登录]
        ProductMgmt[商品管理]
        SupplierMgmt[供应商管理]
        PurchaseMgmt[采购管理]
        SaleMgmt[销售管理]
        InventoryMgmt[库存管理]
        FinanceMgmt[财务管理]
        ReportGen[生成财务报表]
    end
    
    User --> Login
    InventoryManager --> ProductMgmt
    InventoryManager --> SupplierMgmt
    InventoryManager --> PurchaseMgmt
    InventoryManager --> InventoryMgmt
    SalesPerson --> SaleMgmt
    FinancialStaff --> FinanceMgmt
    FinancialStaff --> ReportGen
    Manager --> ReportGen
```

## 2. 核心类图

```mermaid
classDiagram
    class User {
        - id: int
        - username: str
        - email: str
        - password: str
        - role: str
        + __repr__()
    }

    class Product {
        - id: int
        - name: str
        - category: str
        - price: float
        - cost_price: float
        + __repr__()
    }

    class Supplier {
        - id: int
        - name: str
        - contact: str
        - phone: str
        - address: str
        + __repr__()
    }

    class Purchase {
        - id: int
        - product_id: int
        - supplier_id: int
        - quantity: int
        - total_cost: float
        - purchase_date: datetime
        + __repr__()
    }

    class Sale {
        - id: int
        - product_id: int
        - quantity: int
        - total_amount: float
        - sale_date: datetime
        + __repr__()
    }

    class Inventory {
        - id: int
        - product_id: int
        - quantity: int
        - last_updated: datetime
        + __repr__()
    }

    class Expense {
        - id: int
        - description: str
        - amount: float
        - category: str
        - expense_date: datetime
        + __repr__()
    }

    class Income {
        - id: int
        - description: str
        - amount: float
        - category: str
        - income_date: datetime
        + __repr__()
    }

    Product -->|1:N| Purchase
    Product -->|1:N| Sale
    Product -->|1:1| Inventory
    Supplier -->|1:N| Purchase
    Purchase -->|N:1| Product
    Purchase -->|N:1| Supplier
    Sale -->|N:1| Product
    Inventory -->|1:1| Product
```

## 3. 采购流程序列图

```mermaid
sequenceDiagram
    participant 库存管理员
    participant 系统
    
    库存管理员->>系统: 进入添加采购页面
    系统->>库存管理员: 显示采购表单（商品选择、供应商选择、数量输入）
    库存管理员->>系统: 选择商品和供应商，输入采购数量
    系统->>系统: 计算采购总成本（商品成本价 × 数量）
    系统->>系统: 检查商品和供应商是否存在
    系统->>系统: 创建采购记录
    系统->>系统: 更新库存数量（现有数量 + 采购数量）
    系统->>库存管理员: 显示采购成功信息
    系统->>系统: 跳转到采购记录列表页面
```

## 4. 销售流程序列图

```mermaid
sequenceDiagram
    participant 销售人员
    participant 系统
    
    销售人员->>系统: 进入添加销售页面
    系统->>销售人员: 显示销售表单（商品选择、数量输入）
    销售人员->>系统: 选择商品，输入销售数量
    系统->>系统: 检查商品是否存在
    系统->>系统: 检查库存是否充足（库存数量 >= 销售数量）
    系统->>系统: 计算销售总金额（商品售价 × 数量）
    系统->>系统: 创建销售记录
    系统->>系统: 更新库存数量（现有数量 - 销售数量）
    系统->>销售人员: 显示销售成功信息
    系统->>系统: 跳转到销售记录列表页面
```

## 5. 生成财务报表序列图

```mermaid
sequenceDiagram
    participant 财务人员
    participant 系统
    
    财务人员->>系统: 进入财务报表页面
    系统->>系统: 获取当前月份信息
    系统->>系统: 查询本月销售数据
    系统->>系统: 查询本月采购成本数据
    系统->>系统: 查询本月费用数据
    系统->>系统: 查询本月其他收入数据
    系统->>系统: 计算利润表数据
    系统->>系统: 查询库存价值数据
    系统->>系统: 计算资产负债表数据
    系统->>系统: 计算现金流量表数据
    系统->>财务人员: 显示包含三个标签页的财务报表页面
    财务人员->>系统: 点击现金流量表标签
    系统->>财务人员: 切换显示现金流量表数据
    财务人员->>系统: 点击资产负债表标签
    系统->>财务人员: 切换显示资产负债表数据
```

## 6. 数据库关系图

```mermaid
erDiagram

    PRODUCT ||--o{ PURCHASE : 拥有
    PRODUCT ||--o{ SALE : 拥有
    PRODUCT ||--|| INVENTORY : 对应
    SUPPLIER ||--o{ PURCHASE : 提供
    PURCHASE }|--|| PRODUCT : 包含
    PURCHASE }|--|| SUPPLIER : 来自
    SALE }|--|| PRODUCT : 包含
    INVENTORY }|--|| PRODUCT : 对应
    
    USER {
        int id PK
        varchar username
        varchar email
        varchar password
        varchar role
    }
    
    PRODUCT {
        int id PK
        varchar name
        varchar category
        float price
        float cost_price
    }
    
    SUPPLIER {
        int id PK
        varchar name
        varchar contact
        varchar phone
        varchar address
    }
    
    PURCHASE {
        int id PK
        int product_id FK
        int supplier_id FK
        int quantity
        float total_cost
        datetime purchase_date
    }
    
    SALE {
        int id PK
        int product_id FK
        int quantity
        float total_amount
        datetime sale_date
    }
    
    INVENTORY {
        int id PK
        int product_id FK
        int quantity
        datetime last_updated
    }
    
    EXPENSE {
        int id PK
        varchar description
        float amount
        varchar category
        datetime expense_date
    }
    
    INCOME {
        int id PK
        varchar description
        float amount
        varchar category
        datetime income_date
    }
```
