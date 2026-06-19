from __future__ import annotations

import os
from datetime import datetime

from .constants import APP_NAME
from .database import init_db, ensure_accounts, show_accounts, add_account
from .vouchers import create_voucher, list_vouchers, view_voucher_detail
from .accounts import show_trial_balance, set_opening_balance
from .reports import balance_sheet, income_statement, cash_flow_statement, export_excel
from .assets import add_fixed_asset, list_fixed_assets, run_depreciation
from .currency import show_exchange_rates, manual_exchange_rate
from .tax import calc_vat, calc_pit


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def press_any_key():
    input("\n按 Enter 继续...")


def show_main_menu():
    clear_screen()
    print(f"\n{'=' * 44}")
    print(f"  {APP_NAME}")
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    print(f"  {now}")
    print(f"{'=' * 44}")
    print(f"  ┌─ 1. 凭证管理 ──────────────────────┐")
    print(f"  │  1.1 录入凭证                       │")
    print(f"  │  1.2 查看凭证列表                   │")
    print(f"  │  1.3 查看凭证详情                   │")
    print(f"  ├─ 2. 科目管理 ──────────────────────┤")
    print(f"  │  2.1 查看科目表                     │")
    print(f"  │  2.2 新增科目                       │")
    print(f"  │  2.3 试算平衡表                     │")
    print(f"  │  2.4 设置期初余额                   │")
    print(f"  ├─ 3. 财务报表 ──────────────────────┤")
    print(f"  │  3.1 资产负债表                     │")
    print(f"  │  3.2 利润表                         │")
    print(f"  │  3.3 现金流量表                     │")
    print(f"  ├─ 4. 固定资产 ──────────────────────┤")
    print(f"  │  4.1 新增固定资产                   │")
    print(f"  │  4.2 查看固定资产                   │")
    print(f"  │  4.3 计提折旧                       │")
    print(f"  ├─ 5. 多币种管理 ────────────────────┤")
    print(f"  │  5.1 更新汇率                       │")
    print(f"  │  5.2 手动输入汇率                   │")
    print(f"  ├─ 6. 税务计算 ──────────────────────┤")
    print(f"  │  6.1 增值税计算                     │")
    print(f"  │  6.2 个人所得税计算                 │")
    print(f"  ├─ 7. 导出 Excel 报表 ───────────────┤")
    print(f"  │  8. 退出                            │")
    print(f"  └─────────────────────────────────────┘")


def menu_voucher():
    while True:
        clear_screen()
        print("\n── 凭证管理 ──")
        print("  1. 录入新凭证")
        print("  2. 查看凭证列表")
        print("  3. 查看凭证详情")
        print("  4. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            create_voucher()
            press_any_key()
        elif ch == "2":
            y = input("年份 (留空=全部): ").strip()
            m = input("月份 (留空=全部): ").strip()
            list_vouchers(int(y) if y else None, int(m) if m else None)
            press_any_key()
        elif ch == "3":
            view_voucher_detail()
            press_any_key()
        elif ch == "4":
            break


def menu_accounts():
    while True:
        clear_screen()
        print("\n── 科目管理 ──")
        print("  1. 查看科目表")
        print("  2. 新增科目")
        print("  3. 试算平衡表")
        print("  4. 设置期初余额")
        print("  5. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            show_accounts()
            press_any_key()
        elif ch == "2":
            add_account()
            press_any_key()
        elif ch == "3":
            show_trial_balance()
            press_any_key()
        elif ch == "4":
            set_opening_balance()
            press_any_key()
        elif ch == "5":
            break


def menu_reports():
    while True:
        clear_screen()
        print("\n── 财务报表 ──")
        print("  1. 资产负债表")
        print("  2. 利润表")
        print("  3. 现金流量表")
        print("  4. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            balance_sheet()
            press_any_key()
        elif ch == "2":
            income_statement()
            press_any_key()
        elif ch == "3":
            cash_flow_statement()
            press_any_key()
        elif ch == "4":
            break


def menu_assets():
    while True:
        clear_screen()
        print("\n── 固定资产 ──")
        print("  1. 新增固定资产")
        print("  2. 查看固定资产")
        print("  3. 计提折旧")
        print("  4. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            add_fixed_asset()
            press_any_key()
        elif ch == "2":
            list_fixed_assets()
            press_any_key()
        elif ch == "3":
            run_depreciation()
            press_any_key()
        elif ch == "4":
            break


def menu_currency():
    while True:
        clear_screen()
        print("\n── 多币种管理 ──")
        print("  1. 在线更新汇率")
        print("  2. 手动输入汇率")
        print("  3. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            show_exchange_rates()
            press_any_key()
        elif ch == "2":
            manual_exchange_rate()
            press_any_key()
        elif ch == "3":
            break


def menu_tax():
    while True:
        clear_screen()
        print("\n── 税务计算 ──")
        print("  1. 增值税计算")
        print("  2. 个人所得税计算")
        print("  3. 返回主菜单")
        ch = input("请选择: ").strip()
        if ch == "1":
            calc_vat()
            press_any_key()
        elif ch == "2":
            calc_pit()
            press_any_key()
        elif ch == "3":
            break


def main():
    init_db()
    ensure_accounts()

    while True:
        show_main_menu()
        ch = input("\n请选择操作: ").strip()

        if ch == "1" or ch == "1.1":
            create_voucher()
            press_any_key()
        elif ch == "1.2":
            y = input("年份 (留空=全部): ").strip()
            m = input("月份 (留空=全部): ").strip()
            list_vouchers(int(y) if y else None, int(m) if m else None)
            press_any_key()
        elif ch == "1.3":
            view_voucher_detail()
            press_any_key()
        elif ch == "2" or ch == "2.1":
            show_accounts()
            press_any_key()
        elif ch == "2.2":
            add_account()
            press_any_key()
        elif ch == "2.3":
            show_trial_balance()
            press_any_key()
        elif ch == "2.4":
            set_opening_balance()
            press_any_key()
        elif ch == "3" or ch == "3.1":
            balance_sheet()
            press_any_key()
        elif ch == "3.2":
            income_statement()
            press_any_key()
        elif ch == "3.3":
            cash_flow_statement()
            press_any_key()
        elif ch == "4" or ch == "4.1":
            add_fixed_asset()
            press_any_key()
        elif ch == "4.2":
            list_fixed_assets()
            press_any_key()
        elif ch == "4.3":
            run_depreciation()
            press_any_key()
        elif ch == "5" or ch == "5.1":
            show_exchange_rates()
            press_any_key()
        elif ch == "5.2":
            manual_exchange_rate()
            press_any_key()
        elif ch == "6" or ch == "6.1":
            calc_vat()
            press_any_key()
        elif ch == "6.2":
            calc_pit()
            press_any_key()
        elif ch == "7":
            export_excel()
            press_any_key()
        elif ch == "8":
            print("感谢使用会计系统专业版！")
            break
        elif ch == "v":
            menu_voucher()
        elif ch == "a":
            menu_accounts()
        elif ch == "r":
            menu_reports()
        elif ch == "f":
            menu_assets()
        elif ch == "c":
            menu_currency()
        elif ch == "t":
            menu_tax()
        else:
            print("无效选择，请重新输入")


if __name__ == '__main__':
    main()
