from __future__ import annotations

from .auth import CURRENT_USER, login, logout, require_role, get_theme, get_theme_mode, set_theme_mode, load_theme, init_users
from .database import get_db_path, get_excel_path, get_accounts_path, get_conn, init_db, ensure_accounts, load_accounts_from_db, get_account_dict, show_accounts, add_account, _sync_accounts_to_json, init_alert_rules
from .accounts import calc_balances, show_trial_balance, set_opening_balance, get_all_accounts
from .aging import aging_analysis, get_total_ar_ap
from .vouchers import next_voucher_no, create_voucher, show_voucher, list_vouchers, view_voucher_detail, batch_export_vouchers, batch_export_csv, import_vouchers, _import_csv
from .blockchain import init_blockchain, get_chain_length, get_block_by_index, get_chain, _mine_block, add_voucher_to_chain, add_all_vouchers_to_chain, validate_chain, get_chain_stats, export_chain_json, import_chain_json
from .reports import balance_sheet, income_statement, cash_flow_statement, export_excel, _style_header, _style_row, _excel_trial_balance, _excel_balance_sheet, _excel_income_statement, calc_financial_ratios, detect_anomalies, get_smart_suggestions, get_trend_data, predict_next_month, get_template_names, apply_voucher_template
from .period import auto_close_period, ensure_period_table, get_period_status, close_period, get_close_log
from .assets import add_fixed_asset, calc_depreciation, list_fixed_assets, run_depreciation
from .currency import fetch_exchange_rates, show_exchange_rates, manual_exchange_rate
from .tax import calc_vat, calc_pit, compute_vat, compute_pit, PIT_RATES as TAX_PIT_RATES
from .budget import init_budget_tables, set_budget, get_budget_status
from .audit import log_action, get_audit_logs
from .alerts import init_alert_rules as feat_init_alert_rules, add_alert_rule, update_alert_rule, get_alert_rules, _calc_indicator, check_alerts, get_alert_history, resolve_alert
from .backup import backup_database, restore_database
from .reconciliation import import_bank_statement, auto_reconcile, get_reconciliation_status, get_balance_sheet
from .payroll import add_employee, update_employee, get_all_employees, calculate_payroll, confirm_payroll, generate_payroll_voucher, get_payroll_records
from .projects import add_project, get_all_projects, get_project_pnl, link_voucher_to_project
from .cashflow import cash_flow_statement_direct
from .attachments import init_attachment_dir, attach_file, get_attachments, delete_attachment
from .inventory import init_inventory_tables, add_product, update_product, inventory_in, inventory_out, inventory_adjust, get_all_products, get_product, get_inventory_transactions, get_inventory_summary
from .esg import init_esg_tables, get_esg_indicators, get_esg_categories, upsert_esg_data, delete_esg_data, get_esg_data, get_esg_data_map, calc_esg_score_for_indicator, calc_esg_scores, generate_esg_report, export_esg_report_to_file, chart_esg_radar, chart_esg_trend
from .startup import init_micro_ledger, add_micro_entry, delete_micro_entry, get_micro_entries, calc_micro_summary, calc_student_tax, get_student_tax_guide, get_cert_info, generate_study_plan, format_study_plan
from .ai import load_ai_config, save_ai_config, _build_financial_context, call_ai, ask_ai, ai_query_database
from .viz import _fig_to_base64, chart_income_expense, chart_balance_pie, chart_trend_line, chart_ratio_radar, chart_dashboard
from .cli import clear_screen, press_any_key, show_main_menu, menu_voucher, menu_accounts, menu_reports, menu_assets, menu_currency, menu_tax, main as cli_main
from .constants import PIT_RATES, VOUCHER_TEMPLATES, ESG_INDICATORS, CERT_EXAMS

MICRO_CATEGORIES = {
    "餐饮": "餐饮",
    "交通": "交通",
    "购物": "购物",
    "娱乐": "娱乐",
    "学习": "学习",
    "居住": "居住",
    "通讯": "通讯",
    "医疗": "医疗",
    "社交": "社交",
    "其他支出": "其他支出",
}
