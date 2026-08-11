from __future__ import annotations

from ..core.paths import asset_path

from .tokens import COLORS as c, CONST


def app_qss() -> str:
    check_icon = asset_path("icons", "checkmark.svg").as_posix()
    chevron_down = asset_path("icons", "chevron-down.svg").as_posix()
    chevron_up = asset_path("icons", "chevron-up.svg").as_posix()
    return f"""
    * {{
        font-family: 'Segoe UI Variable', 'Segoe UI';
        font-size: 12px;
        color: {c['primary_text']};
        outline: 0;
    }}
    QMainWindow, QDialog {{ background: {c['window_background']}; }}
    QWidget#AppRoot, QWidget#PageViewport, QWidget#PageContent, QWidget#PageInner {{
        background: {c['page_background']}; border: none;
    }}
    QWidget#WindowHeader, QFrame#WindowHeader {{
        background: {c['window_background']};
        border-bottom: 1px solid {c['border']};
        min-height: {CONST.header_height}px;
        max-height: {CONST.header_height}px;
    }}
    QScrollArea, QScrollArea::viewport {{ background: transparent; border: none; }}
    QScrollArea#MinimalScrollArea, QScrollArea#MinimalScrollArea::viewport {{
        background: {c['page_background']}; border: none;
    }}
    QWidget#SettingsContent, QWidget#DialogContent {{
        background: {c['page_background']}; border: none;
    }}
    QWidget#Sidebar QScrollArea#MinimalScrollArea,
    QWidget#Sidebar QScrollArea#MinimalScrollArea::viewport,
    QWidget#Sidebar QWidget#SidebarNavHost {{
        background: {c['window_background']};
        border: none;
    }}
    QWidget#Sidebar QScrollArea#MinimalScrollArea {{ padding-right: 0px; }}
    QWidget#Sidebar, QFrame#Sidebar {{
        background: {c['window_background']};
        border-right: 1px solid {c['border']};
        min-width: {CONST.sidebar_width}px;
        max-width: {CONST.sidebar_width}px;
    }}
    QLabel {{ background: transparent; color: {c['primary_text']}; }}
    QLabel#WindowTitle {{ font-size: 14px; font-weight: 500; color: {c['title_text']}; }}
    QLabel#SidebarTitle {{ font-size: 13px; font-weight: 600; color: {c['title_text']}; }}
    QLabel#PageTitle {{ font-size: 15px; font-weight: 600; color: {c['title_text']}; }}
    QLabel#SectionTitle, QLabel#CardTitle {{ font-size: 13px; font-weight: 600; color: {c['title_text']}; }}
    QLabel#Description {{ font-size: 12px; color: {c['secondary_text']}; }}
    QLabel#Caption, QLabel#Muted, QLabel#Breadcrumb {{ font-size: 11px; color: {c['secondary_text']}; }}
    QLabel#FormLabel {{ font-size: 11px; font-weight: 600; color: {c['secondary_text']}; }}
    QLabel#MetricValue {{ font-size: 15px; font-weight: 600; color: {c['primary_text']}; }}
    QLabel#MetricValueSuccess {{ font-size: 15px; font-weight: 600; color: {c['success']}; }}
    QLabel#MetricValueDanger {{ font-size: 15px; font-weight: 600; color: #EF4444; }}
    QLabel#StatusBadge, QLabel#TokenChip {{
        background: #1E293B;
        color: {c['secondary_text']};
        border: 1px solid #334155;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 10px;
        font-weight: 600;
    }}
    QLabel#StatusBadgeSuccess {{ background: rgba(22,101,52,64); color: #86EFAC; border: 1px solid rgba(34,197,94,76); border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; }}
    QLabel#StatusBadgeWarning {{ background: rgba(245,158,11,35); color: #FCD34D; border: 1px solid rgba(245,158,11,70); border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; }}
    QLabel#StatusBadgeDanger {{ background: rgba(185,28,28,45); color: #FCA5A5; border: 1px solid rgba(239,68,68,80); border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; }}
    QFrame#Card, QFrame#Panel {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: {CONST.common_radius}px;
    }}
    QFrame#PluginCard {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: {CONST.common_radius}px;
    }}
    QFrame#PluginCard:hover {{
        background: {c['nested_surface']};
        border: 1px solid {c['border']};
    }}
    QLabel#PluginCardTitle {{
        font-size: 13px;
        font-weight: 600;
        color: {c['title_text']};
    }}
    QLabel#PluginCardDescription {{
        font-size: 11px;
        font-weight: 400;
        color: {c['secondary_text']};
    }}
    QLabel#ProviderLogo {{
        background: transparent;
        border: none;
    }}
    QLabel#ProviderVersionText {{
        font-size: 9px;
        font-weight: 500;
        color: {c['muted_text']};
    }}
    QFrame#PluginCard QLabel#StatusBadge {{
        background: #1E293B;
        color: {c['secondary_text']};
        border: 1px solid #263244;
        border-radius: 4px;
        padding: 1px 5px;
        font-size: 9px;
        font-weight: 600;
    }}
    QFrame#PluginCard QLabel#StatusBadgeSuccess {{
        border-radius: 4px;
        padding: 1px 5px;
        font-size: 9px;
        font-weight: 600;
    }}
    QFrame#NestedCard, QFrame#MetricCard {{
        background: {c['nested_surface']};
        border: 1px solid {c['border']};
        border-radius: {CONST.common_radius}px;
    }}
    QFrame#Divider {{ background: {c['border']}; border: none; min-height: 1px; max-height: 1px; }}
    QPushButton {{
        min-height: {CONST.button_height}px;
        max-height: {CONST.button_height}px;
        border-radius: {CONST.common_radius}px;
        border: 1px solid {c['button_border']};
        background: {c['nested_surface']};
        color: {c['primary_text']};
        padding: 0px {CONST.button_padding_x}px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{ background: #202938; }}
    QPushButton:pressed {{ background: #151B26; }}
    QPushButton:focus {{ border: 2px solid {c['focus']}; padding: 0px {CONST.button_padding_x - 1}px; }}
    QPushButton:disabled {{ color: {c['disabled_text']}; background: {c['surface']}; border-color: {c['border']}; }}
    QPushButton#PrimaryButton {{ background: {c['primary']}; border-color: rgba(255,255,255,31); }}
    QPushButton#PrimaryButton:hover {{ background: {c['primary_hover']}; }}
    QPushButton#PrimaryButton:pressed {{ background: {c['primary_pressed']}; }}
    QPushButton#ProviderLoadButton {{
        background: {c['primary']};
        border-color: {c['focus']};
        color: {c['primary_text']};
        font-weight: 600;
    }}
    QPushButton#ProviderLoadButton:hover {{ background: {c['primary_hover']}; }}
    QPushButton#ProviderLoadButton:pressed {{ background: {c['primary_pressed']}; }}
    QPushButton#ProviderUninstallButton {{
        background: transparent;
        border-color: {c['primary']};
        color: {c['primary_hover']};
    }}
    QPushButton#ProviderUninstallButton:hover {{
        background: rgba(37,99,235,31);
        border-color: {c['primary_hover']};
        color: {c['primary_text']};
    }}
    QPushButton#ProviderUninstallButton:pressed {{
        background: {c['primary_pressed']};
        border-color: {c['primary_pressed']};
        color: {c['primary_text']};
    }}
    QPushButton#DangerButton {{ background: transparent; border-color: {c['danger']}; color: #FCA5A5; }}
    QPushButton#DangerButton:hover {{ background: rgba(185,28,28,31); }}
    QPushButton#GhostButton {{ background: transparent; border-color: transparent; color: {c['secondary_text']}; }}
    QPushButton#GhostButton:hover {{ background: {c['hover']}; color: {c['primary_text']}; }}
    QPushButton#NavItem {{
        min-height: {CONST.nav_height}px; max-height: {CONST.nav_height}px;
        text-align: left; background: transparent; border: 1px solid transparent;
        border-radius: 7px; padding: 2px 8px; color: {c['secondary_text']};
    }}
    QPushButton#NavItem:hover {{ background: {c['hover']}; color: {c['primary_text']}; }}
    QPushButton#NavItem:checked {{
        background: {c['nav_selected']}; color: {c['primary_text']}; font-weight: 600;
        border-left: 2px solid {c['focus']}; padding-left: 6px;
    }}
    QLineEdit#ProviderSearchInput {{
        background: {c['nested_surface']};
        border-color: {c['input_border']};
    }}
    QLineEdit#ProviderSearchInput:focus {{ border-color: {c['focus']}; }}
    QLineEdit, QComboBox, QSpinBox {{
        min-height: {CONST.input_height}px; max-height: {CONST.input_height}px;
        border-radius: {CONST.common_radius}px; border: 1px solid {c['input_border']};
        background: {c['input_background']}; color: {c['primary_text']};
        padding: 0px 10px; selection-background-color: {c['selection']};
    }}
    QTextEdit, QPlainTextEdit {{
        border-radius: {CONST.common_radius}px; border: 1px solid {c['input_border']};
        background: {c['input_background']}; color: {c['primary_text']}; padding: 7px 10px;
        selection-background-color: {c['selection']};
    }}
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QTextEdit:hover, QPlainTextEdit:hover {{ border-color: #334155; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {c['focus']}; }}
    QComboBox QAbstractItemView {{
        background: {c['surface']}; color: {c['primary_text']};
        border: 1px solid {c['input_border']};
        selection-background-color: {c['selection']}; selection-color: {c['primary_text']};
    }}
    QListWidget {{
        background: {c['surface']}; color: {c['primary_text']};
        border: 1px solid {c['border']}; border-radius: {CONST.common_radius}px;
        selection-background-color: {c['selection']}; selection-color: {c['primary_text']};
        font-size: 12px; font-weight: 400;
    }}
    QListWidget::item {{ min-height: {CONST.table_row_height}px; padding: 0px 7px; color: {c['primary_text']}; }}
    QListWidget::item:hover {{ background: {c['row_hover']}; }}
    QListWidget::item:selected {{ background: {c['selection']}; color: {c['primary_text']}; }}
    QListWidget::item:disabled {{ color: {c['disabled_text']}; background: {c['surface']}; }}
    QMenu {{
        background: {c['surface']}; color: {c['primary_text']};
        border: 1px solid {c['border']}; padding: 4px;
    }}
    QMenu::item {{ background: transparent; color: {c['primary_text']}; padding: 6px 24px 6px 10px; }}
    QMenu::item:selected {{ background: {c['primary']}; color: {c['primary_text']}; }}
    QMenu::item:disabled {{ color: {c['disabled_text']}; }}
    QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 6px; }}
    QAbstractItemView#CurrencySearchResults {{
        background: {c['surface']}; color: {c['primary_text']};
        border: 1px solid {c['input_border']};
        selection-background-color: {c['selection']};
        selection-color: {c['primary_text']};
    }}
    QAbstractItemView#CurrencySearchResults::item {{
        min-height: 26px; padding: 0px 8px;
    }}
    QCheckBox {{ spacing: 8px; color: {c['primary_text']}; }}
    QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 4px; border: 1px solid #30363D; background: {c['window_background']}; }}
    QCheckBox::indicator:checked {{
        background: {c['primary']};
        border-color: {c['primary_hover']};
        image: url("{check_icon}");
    }}
    QTreeWidget, QTableWidget {{
        background: {c['surface']}; alternate-background-color: {c['row_alternate']};
        border: 1px solid {c['border']}; border-radius: {CONST.common_radius}px;
        gridline-color: transparent; selection-background-color: {c['selection']};
        selection-color: {c['primary_text']}; color: {c['primary_text']};
        font-size: 12px; font-weight: 400;
    }}
    QTreeWidget::item, QTableWidget::item {{
        min-height: {CONST.table_row_height}px; padding: 0px 7px;
        border-bottom: 1px solid {c['border']};
    }}
    QTreeWidget::item:hover, QTableWidget::item:hover {{ background: {c['row_hover']}; }}
    QHeaderView::section {{
        background: {c['table_header']}; color: {c['secondary_text']}; border: none;
        border-bottom: 1px solid {c['data_divider']}; padding: 0px 7px;
        min-height: {CONST.table_header_height}px; max-height: {CONST.table_header_height}px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.2px;
    }}

    /* v1.42.0 Global Forms + Settings scoped compact design contract. */
    QDialog QLabel,
    QWidget#SettingsPage QLabel {{ color: {c['text_body']}; }}
    QDialog QLabel#PageTitle,
    QWidget#SettingsPage QLabel#PageTitle {{
        font-size: 15px; font-weight: 500; color: {c['text_title']};
    }}
    QDialog QLabel#SectionTitle,
    QDialog QLabel#CardTitle,
    QWidget#SettingsPage QLabel#SectionTitle,
    QWidget#SettingsPage QLabel#CardTitle {{
        font-size: 13px; font-weight: 500; color: {c['text_title']};
    }}
    QDialog QLabel#Description,
    QWidget#SettingsPage QLabel#Description {{
        font-size: 12px; font-weight: 400; color: {c['text_body']};
    }}
    QDialog QLabel#Caption,
    QDialog QLabel#Muted,
    QDialog QLabel#FormLabel,
    QWidget#SettingsPage QLabel#Caption,
    QWidget#SettingsPage QLabel#Muted,
    QWidget#SettingsPage QLabel#FormLabel {{
        font-size: 11px; font-weight: 500; color: {c['text_muted']};
    }}
    QDialog QLineEdit,
    QDialog QComboBox,
    QDialog QSpinBox,
    QWidget#SettingsPage QLineEdit,
    QWidget#SettingsPage QComboBox,
    QWidget#SettingsPage QSpinBox {{
        min-height: {CONST.form_control_height}px;
        max-height: {CONST.form_control_height}px;
        border-radius: {CONST.form_radius}px;
        border: 1px solid {c['input_border']};
        background: {c['input_background']};
        color: {c['text_body']};
        padding: 0px 9px;
        font-weight: 400;
        placeholder-text-color: {c['text_placeholder']};
        selection-background-color: {c['selection']};
    }}
    QDialog QTextEdit,
    QDialog QPlainTextEdit,
    QWidget#SettingsPage QTextEdit,
    QWidget#SettingsPage QPlainTextEdit {{
        border-radius: {CONST.form_radius}px;
        color: {c['text_body']};
        font-weight: 400;
        placeholder-text-color: {c['text_placeholder']};
    }}
    QDialog QPushButton,
    QWidget#SettingsPage QPushButton {{
        min-height: {CONST.form_control_height}px;
        max-height: {CONST.form_control_height}px;
        border-radius: {CONST.form_radius}px;
        font-size: 12px;
        font-weight: 500;
    }}
    QDialog QPushButton#PrimaryButton,
    QWidget#SettingsPage QPushButton#PrimaryButton {{
        background: {c['primary']};
        border-color: rgba(255,255,255,31);
        color: #FFFFFF;
        font-weight: 500;
    }}
    QDialog QFrame#Card,
    QWidget#SettingsPage QFrame#Card[settingsCard="true"] {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: {CONST.form_radius}px;
    }}
    QDialog QListWidget,
    QDialog QTableWidget {{ border-radius: {CONST.form_radius}px; }}
    QDialog QCheckBox,
    QWidget#SettingsPage QCheckBox {{ color: {c['text_body']}; font-weight: 400; }}
    QWidget#SettingsHeader {{ background: transparent; border: none; }}
    QWidget#SettingsPage QLineEdit#SettingsSearchInput {{
        background: {c['nested_surface']};
        color: {c['text_body']};
        border-color: {c['input_border']};
        placeholder-text-color: {c['text_placeholder']};
    }}
    QWidget#SettingsPage QLineEdit#SettingsSearchInput:focus {{ border-color: {c['focus']}; }}
    QWidget#SettingsPage QPushButton#SettingsResetButton {{
        background: {c['nested_surface']};
        border-color: {c['button_border']};
        color: {c['danger_text']};
    }}
    QWidget#SettingsPage QPushButton#SettingsResetButton:hover {{
        background: rgba(185,28,28,20);
        border-color: {c['danger']};
    }}
    QWidget#SettingsPage QPushButton#SettingsResetButton:pressed {{
        background: rgba(185,28,28,35);
        border-color: {c['danger']};
    }}
    QPlainTextEdit#LogViewer {{ background: {c['nested_surface']}; border: 1px solid {c['input_border']}; padding: 10px 12px; }}
    QTableWidget#ReportTable, QTableWidget#RecipientReportTable {{ background: {c['surface']}; border-radius: {CONST.common_radius}px; }}
    QTableWidget#InvoiceItemsTable {{ background: {c['surface']}; }}


    /* v1.43.0 compact Data Grid contract. */
    QWidget[dataPage="true"] QLabel#PageTitle,
    QWidget[dataPage="true"] QLabel#SectionTitle,
    QWidget[dataPage="true"] QLabel#CardTitle {{
        color: {c['text_title']};
        font-weight: 500;
    }}
    QWidget[dataPage="true"] QLabel#Description {{
        color: {c['text_body']};
        font-weight: 400;
    }}
    QWidget#DataGridToolbar,
    QWidget#DataGridFooter,
    QWidget#DataGridBadgeHost {{
        background: transparent;
        border: none;
    }}
    QWidget#DataGridToolbar {{
        border-bottom: 1px solid {c['data_divider']};
        padding-bottom: {CONST.data_grid_padding}px;
    }}
    QWidget#DataGridFooter {{
        border-top: 1px solid {c['data_divider']};
        padding-top: {CONST.data_grid_padding}px;
    }}
    QLineEdit#DataGridSearchInput,
    QComboBox#DataGridFilter,
    QComboBox#DataGridPageSize {{
        min-height: {CONST.data_grid_control_height}px;
        max-height: {CONST.data_grid_control_height}px;
        border-radius: 6px;
        border: 1px solid {c['input_border']};
        background: {c['nested_surface']};
        color: {c['text_body']};
        padding: 0px 8px;
        font-size: 11px;
        font-weight: 400;
        placeholder-text-color: {c['text_placeholder']};
    }}
    QLineEdit#DataGridSearchInput:focus,
    QComboBox#DataGridFilter:focus,
    QComboBox#DataGridPageSize:focus {{
        border-color: {c['focus']};
    }}
    QComboBox#DataGridFilter {{ min-width: 118px; }}
    QComboBox#DataGridPageSize {{ min-width: 52px; max-width: 62px; }}
    QLabel#DataGridMeta,
    QLabel#DataGridEmpty {{
        color: {c['text_muted']};
        font-size: 11px;
        font-weight: 400;
    }}
    QPushButton#DataGridPageButton {{
        min-width: {CONST.data_grid_control_height}px;
        max-width: {CONST.data_grid_control_height}px;
        min-height: {CONST.data_grid_control_height}px;
        max-height: {CONST.data_grid_control_height}px;
        padding: 0px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#DataGridPageButton[currentPage="true"] {{
        background: {c['primary']};
        border-color: {c['primary_hover']};
        color: #FFFFFF;
    }}
    QLabel#DataGridStatusSuccess,
    QLabel#DataGridStatusDanger,
    QLabel#DataGridStatusWarning,
    QLabel#DataGridStatusNeutral {{
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 10px;
        font-weight: 500;
    }}
    QLabel#DataGridStatusSuccess {{ background: #064E3B; color: #34D399; }}
    QLabel#DataGridStatusDanger {{ background: #7F1D1D; color: #F87171; }}
    QLabel#DataGridStatusWarning {{ background: #78350F; color: #FBBF24; }}
    QLabel#DataGridStatusNeutral {{ background: #1E293B; color: {c['text_muted']}; }}
    QPushButton#TableActionButton {{
        min-height: 28px;
        max-height: 28px;
        border-radius: 6px;
        padding: 0px 5px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#TableActionDangerButton {{
        min-height: 28px;
        max-height: 28px;
        border-radius: 6px;
        padding: 0px 5px;
        font-size: 11px;
        font-weight: 500;
        background: transparent;
        border: 1px solid {c['danger']};
        color: {c['danger_text']};
    }}
    QPushButton#TableActionDangerButton:hover {{ background: rgba(185,28,28,31); }}
    QTableWidget#NewTaskAccountsTable::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 4px;
        border: 1px solid #30363D;
        background: {c['window_background']};
    }}
    QTableWidget#NewTaskAccountsTable::indicator:checked {{
        background: {c['primary']};
        border-color: {c['primary_hover']};
        image: url("{check_icon}");
    }}

    /* v1.46.0 custom frameless window chrome. */
    QMainWindow#InvioMainWindow {{
        background: {c['window_background']};
        border: 1px solid {c['border']};
    }}
    QDialog[customChrome="true"] {{
        background: {c['window_background']};
        border: 1px solid {c['input_border']};
    }}
    QFrame#MainTitleBar {{
        background: #0D121B;
        border: none;
        border-bottom: 1px solid {c['border']};
    }}
    QFrame#DialogTitleBar {{
        background: {c['surface']};
        border: none;
        border-bottom: 1px solid {c['border']};
    }}
    QLabel#TitleBarIcon {{ background: transparent; border: none; }}
    QLabel#MainTitleText {{
        color: {c['text_title']};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#MainTitleContext {{
        color: {c['text_muted']};
        font-size: 11px;
        font-weight: 400;
    }}
    QLabel#MainTitleBrand {{
        background: #1E293B;
        color: {c['secondary_text']};
        border: 1px solid #334155;
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 9px;
        font-weight: 500;
    }}
    QLabel#DialogTitleText {{
        color: {c['text_title']};
        font-size: 12px;
        font-weight: 500;
    }}
    QFrame#MainTitleBar QPushButton,
    QFrame#DialogTitleBar QPushButton {{
        min-width: 0px;
        background: transparent;
        color: {c['secondary_text']};
        border: none;
        border-radius: 0px;
        padding: 0px;
        font-size: 13px;
        font-weight: 400;
    }}
    QFrame#MainTitleBar QPushButton {{
        min-height: {CONST.main_titlebar_height}px;
        max-height: {CONST.main_titlebar_height}px;
    }}
    QFrame#DialogTitleBar QPushButton {{
        min-height: {CONST.dialog_titlebar_height}px;
        max-height: {CONST.dialog_titlebar_height}px;
    }}
    QFrame#MainTitleBar QPushButton:hover,
    QFrame#DialogTitleBar QPushButton:hover {{
        background: {c['hover']};
        color: {c['primary_text']};
    }}
    QPushButton#MainTitleClose:hover,
    QPushButton#DialogTitleClose:hover {{
        background: {c['danger']};
        color: #FFFFFF;
    }}
    QPushButton#MainTitleClose:pressed,
    QPushButton#DialogTitleClose:pressed {{
        background: {c['danger_hover']};
        color: #FFFFFF;
    }}

    /* v1.47.0 Vib Tools desktop design-system refinement. */
    QWidget#ModalOverlay {{
        background: rgba(0, 0, 0, 82);
        border: none;
    }}
    QWidget#DialogBody {{
        background: transparent;
        border: none;
    }}
    QWidget#DialogActionFooter {{
        background: transparent;
        border: none;
        border-top: 1px solid #1E2633;
    }}
    QFrame#PageHeader {{
        background: transparent;
        border: none;
    }}
    QLabel#PageTitle {{
        font-size: 15px;
        font-weight: 500;
        color: #E6EDF3;
    }}
    QLabel#SectionTitle, QLabel#CardTitle {{
        font-size: 13px;
        font-weight: 500;
        color: #E6EDF3;
    }}
    QLabel#Description {{
        font-size: 12px;
        font-weight: 400;
        color: #C9D1D9;
    }}
    QLabel#Caption, QLabel#Muted, QLabel#Breadcrumb, QLabel#FormLabel {{
        color: #8B949E;
    }}
    QLabel#FormLabel {{
        font-size: 11px;
        font-weight: 500;
    }}
    QLabel#SidebarSectionLabel {{
        color: #64748B;
        font-size: 9px;
        font-weight: 500;
        padding: 4px 8px 2px 8px;
    }}
    QFrame#SidebarFooter {{
        background: #0D121B;
        border: 1px solid #18202C;
        border-radius: 6px;
    }}
    QLabel#SidebarFooterTitle {{
        color: #E6EDF3;
        font-size: 11px;
        font-weight: 500;
    }}
    QLabel#SidebarFooterMeta {{
        color: #64748B;
        font-size: 9px;
        font-weight: 400;
    }}
    QPushButton#NavItem {{
        min-height: 28px;
        max-height: 28px;
        border-radius: 6px;
        padding: 1px 8px;
        font-size: 11px;
        font-weight: 400;
        color: #C9D1D9;
    }}
    QPushButton#NavItem:hover {{
        background: rgba(255,255,255,10);
        color: #F8FAFC;
    }}
    QPushButton#NavItem:checked {{
        background: rgba(37,99,235,34);
        color: #F8FAFC;
        font-weight: 500;
        border: 1px solid rgba(59,130,246,40);
        border-left: 2px solid #38BDF8;
        padding-left: 7px;
    }}
    QFrame#Card, QFrame#Panel {{
        background: #111722;
        border-color: #1E2633;
        border-radius: 8px;
    }}
    QFrame#NestedCard, QFrame#MetricCard {{
        background: #151C27;
        border-color: #1E2633;
        border-radius: 8px;
    }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        font-weight: 400;
    }}
    QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        color: #64748B;
        background: #111722;
        border-color: #1E2633;
    }}
    QLineEdit[readOnly="true"], QTextEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {{
        color: #94A3B8;
        background: #111722;
        border-color: #1E2633;
    }}
    QLineEdit[validationState="error"], QComboBox[validationState="error"], QSpinBox[validationState="error"], QTextEdit[validationState="error"] {{
        border-color: #B91C1C;
    }}
    QLineEdit[validationState="success"], QComboBox[validationState="success"], QSpinBox[validationState="success"], QTextEdit[validationState="success"] {{
        border-color: #166534;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border: none;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: url("{chevron_down}");
        width: 14px;
        height: 14px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 22px;
        border: none;
        background: transparent;
    }}
    QSpinBox::up-arrow {{
        image: url("{chevron_up}");
        width: 12px;
        height: 12px;
    }}
    QSpinBox::down-arrow {{
        image: url("{chevron_down}");
        width: 12px;
        height: 12px;
    }}
    QCheckBox:hover {{ color: #F8FAFC; }}
    QCheckBox:focus {{ color: #F8FAFC; }}
    QPushButton#GhostButton {{
        background: transparent;
        border-color: #283345;
        color: #C9D1D9;
    }}
    QPushButton#GhostButton:hover {{
        background: rgba(255,255,255,8);
        border-color: #334155;
        color: #F8FAFC;
    }}
    QLabel#InlineStatusNeutral,
    QLabel#InlineStatusInfo,
    QLabel#InlineStatusSuccess,
    QLabel#InlineStatusWarning,
    QLabel#InlineStatusDanger {{
        font-size: 11px;
        font-weight: 400;
        padding: 2px 0px;
    }}
    QLabel#InlineStatusNeutral {{ color: #8B949E; }}
    QLabel#InlineStatusInfo {{ color: #93C5FD; }}
    QLabel#InlineStatusSuccess {{ color: #34D399; }}
    QLabel#InlineStatusWarning {{ color: #FBBF24; }}
    QLabel#InlineStatusDanger {{ color: #F87171; }}
    QFrame#MainTitleBar {{
        background: #0B111A;
        border-bottom: 1px solid #1E2633;
    }}
    QFrame#DialogTitleBar {{
        background: #111722;
        border-bottom: 1px solid #263244;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QFrame#TitleBarContextDivider {{
        background: #263244;
        border: none;
    }}
    QLabel#MainTitleText, QLabel#DialogTitleText {{
        color: #E6EDF3;
        font-weight: 500;
    }}
    QLabel#MainTitleContext {{
        color: #8B949E;
        font-size: 10px;
        font-weight: 400;
    }}
    QLabel#MainTitleBrand {{
        background: transparent;
        color: #C9D1D9;
        border: none;
        padding: 0px 7px;
        font-size: 10px;
        font-weight: 500;
    }}
    QDialog[customChrome="true"] {{
        background: transparent;
        border: none;
    }}
    QFrame#DialogSurface {{
        background: #090D14;
        border: 1px solid #2D3748;
        border-radius: 8px;
    }}
    QFrame#MainTitleBar QPushButton,
    QFrame#DialogTitleBar QPushButton {{
        border-radius: 4px;
    }}
    QFrame#MainTitleBar QPushButton:hover,
    QFrame#DialogTitleBar QPushButton:hover {{
        background: rgba(255,255,255,10);
    }}
    QTableWidget, QTreeWidget, QListWidget {{
        border-color: #1E2633;
        selection-background-color: rgba(37,99,235,38);
    }}
    QHeaderView::section {{
        color: #CBD5E1;
        font-size: 11px;
        font-weight: 600;
    }}
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover {{
        background: #475569;
    }}

    QProgressBar {{
        min-height: 6px; max-height: 6px; border: none; background: {c['border']}; border-radius: 3px; text-align: center;
    }}
    QProgressBar::chunk {{ background: {c['primary']}; border-radius: 3px; }}
    QStatusBar {{ background: {c['window_background']}; color: {c['secondary_text']}; border-top: 1px solid {c['border']}; min-height: {CONST.status_height}px; max-height: {CONST.status_height}px; }}
    QStatusBar::item {{ border: none; }}
    QSplitter::handle {{ background: {c['border']}; width: 1px; }}
    QToolTip {{ background: {c['surface']}; color: {c['primary_text']}; border: 1px solid {c['border']}; padding: 5px 7px; }}
    QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: #334155; border-radius: 3px; min-height: 28px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar:horizontal {{ background: transparent; height: 6px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: #334155; border-radius: 3px; min-width: 28px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
    """
