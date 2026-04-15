DROP DATABASE IF EXISTS RestaurantBACED;
CREATE DATABASE IF NOT EXISTS RestaurantBACED;
USE RestaurantBACED;

CREATE TABLE IF NOT EXISTS roles (
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    role_name   VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permissions (
    permissions_id   INT AUTO_INCREMENT PRIMARY KEY,
    permissions_name VARCHAR(100) NOT NULL,
    description      VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INT NOT NULL,
    permission_id INT NOT NULL,
    CONSTRAINT pk_rp      PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_rp_role FOREIGN KEY (role_id)       REFERENCES roles(role_id),
    CONSTRAINT fk_rp_perm FOREIGN KEY (permission_id) REFERENCES permissions(permissions_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name    VARCHAR(255) NOT NULL,
    email   VARCHAR(255) UNIQUE,
    role_id INT NOT NULL,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) UNIQUE,
    phone_number  VARCHAR(50)  UNIQUE
);

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id   INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(255)  NOT NULL,
    supplier_id     INT           NOT NULL,
    unit            VARCHAR(30),
    cost_per_unit   DECIMAL(10,2) NOT NULL,
    quantity        DECIMAL(10,2) NOT NULL DEFAULT 0,
    reorder_count   DECIMAL(10,2) NOT NULL DEFAULT 0,
    expiration_date DATE,
    CONSTRAINT fk_ingredient_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE IF NOT EXISTS menu_items (
    menu_item_id        INT AUTO_INCREMENT PRIMARY KEY,
    item_name           VARCHAR(255)  NOT NULL,
    description         TEXT,
    availability_status VARCHAR(20)   NOT NULL DEFAULT 'available'
        CHECK (availability_status IN ('available', 'unavailable', 'archived')),
    price               DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS tables (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    capacity INT         NOT NULL,
    status   VARCHAR(20) NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'occupied', 'reserved', 'out_of_service')),
    section  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS kitchen_orders (
    order_id   INT AUTO_INCREMENT PRIMARY KEY,
    table_id   INT         NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
    waiter_id  INT         NOT NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filled_at  TIMESTAMP   NULL,
    notes      TEXT,
    CONSTRAINT fk_ko_table  FOREIGN KEY (table_id)  REFERENCES tables(table_id),
    CONSTRAINT fk_ko_waiter FOREIGN KEY (waiter_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT NOT NULL,
    menu_item_id  INT NOT NULL,
    special_notes TEXT,
    CONSTRAINT fk_oi_order     FOREIGN KEY (order_id)     REFERENCES kitchen_orders(order_id),
    CONSTRAINT fk_oi_menu_item FOREIGN KEY (menu_item_id) REFERENCES menu_items(menu_item_id)
);

CREATE TABLE IF NOT EXISTS supplier_prices (
    price_id       INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id    INT           NOT NULL,
    ingredient_id  INT           NOT NULL,
    previous_price DECIMAL(10,2) NOT NULL,
    current_price  DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_sp_supplier   FOREIGN KEY (supplier_id)   REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_sp_ingredient FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

CREATE TABLE IF NOT EXISTS expected_usage (
    usage_id          INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id     INT           NOT NULL,
    expected_quantity DECIMAL(10,2) NOT NULL,
    time_period       VARCHAR(30)   NOT NULL,
    start_timestamp   TIMESTAMP     NOT NULL,
    CONSTRAINT fk_eu_ingredient FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    alert_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT       NOT NULL,
    message    TEXT      NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read    BOOLEAN   NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_notice_recipient FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS activity_log (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT         NOT NULL,
    action      VARCHAR(50) NOT NULL,
    action_time TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details     TEXT,
    CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
