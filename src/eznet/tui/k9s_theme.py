"""
EZNet TUI - k9s-style CSS Theme.

This module provides CSS styling to make the TUI look more like k9s.
"""

K9S_THEME = """
/* k9s-inspired color scheme */
Screen {
    background: #1a1a1a;
    color: #f0f0f0;
}

/* Header styling similar to k9s */
Header {
    background: #4ecdc4;
    color: #ffffff;
    text-style: bold;
}

Footer {
    background: #2d3748;
    color: #e2e8f0;
}

/* Breadcrumb navigation */
#breadcrumbs {
    background: #2d3748;
    color: #cbd5e0;
    height: 1;
    padding: 0 1;
    text-style: dim;
}

/* Data tables - k9s style */
DataTable {
    background: #1a202c;
    color: #e2e8f0;
    border: solid #4a5568;
    scrollbar-background: #2d3748;
    scrollbar-color: #4a5568;
}

DataTable > .datatable--header {
    background: #2d3748;
    color: #63b3ed;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #3182ce;
    color: #ffffff;
    text-style: bold;
}

DataTable > .datatable--hover {
    background: #2a69ac;
}

/* Info panel */
#info-panel {
    background: #1a202c;
    border: solid #4a5568;
    padding: 1;
    color: #e2e8f0;
    width: 65%;
}

/* Host table container */
#host-container {
    width: 35%;
}

/* Scrollable info container */
#info-scroll {
    height: 100%;
    scrollbar-background: #2d3748;
    scrollbar-color: #4a5568;
    scrollbar-color-hover: #63b3ed;
    scrollbar-color-active: #3182ce;
}

/* Status and menu bars */
#status-bar {
    background: #3182ce;
    color: #ffffff;
    height: 1;
    text-align: center;
    text-style: bold;
}

#menu-bar {
    background: #2d3748;
    color: #e2e8f0;
    height: 1;
    padding: 0 1;
}

/* Panel titles */
.panel-title {
    background: #4a5568;
    color: #63b3ed;
    text-align: center;
    text-style: bold;
    height: 1;
    margin-bottom: 1;
    border: solid #4a5568;
}

/* Buttons - k9s style */
Button {
    background: #3182ce;
    color: #ffffff;
    border: solid #2c5282;
    margin: 0 1;
}

Button:hover {
    background: #2c5282;
    text-style: bold;
}

Button.-primary {
    background: #38a169;
    border: solid #2f855a;
}

Button.-primary:hover {
    background: #2f855a;
}

/* Input fields */
Input {
    background: #2d3748;
    color: #e2e8f0;
    border: solid #4a5568;
}

Input:focus {
    border: solid #63b3ed;
}

/* Modal dialogs */
#add-host-dialog {
    background: #1a202c;
    border: solid #63b3ed;
}

.dialog-title {
    color: #63b3ed;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

.input-label {
    color: #cbd5e0;
    margin-bottom: 1;
}

/* Results screen styling */
ResultsScreen {
    background: #1a202c;
    border: solid #4a5568;
    padding: 1;
}

.results-title {
    background: #3182ce;
    color: #ffffff;
    text-align: center;
    text-style: bold;
    height: 1;
    margin-bottom: 1;
}

/* Tabbed content */
TabbedContent {
    background: #1a202c;
}

TabPane {
    background: #1a202c;
    color: #e2e8f0;
    padding: 1;
}

Tabs {
    background: #2d3748;
}

Tab {
    background: #2d3748;
    color: #cbd5e0;
    padding: 0 2;
}

Tab:hover {
    background: #4a5568;
    color: #e2e8f0;
}

Tab.-active {
    background: #3182ce;
    color: #ffffff;
    text-style: bold;
}

/* Success/Error colors similar to k9s */
.success {
    color: #68d391;
    text-style: bold;
}

.error {
    color: #f56565;
    text-style: bold;
}

.warning {
    color: #f6ad55;
    text-style: bold;
}

.info {
    color: #63b3ed;
    text-style: bold;
}

.dim {
    color: #718096;
    text-style: dim;
}

/* Scrollbars */
ScrollView > .scrollbar--vertical {
    background: #2d3748;
}

ScrollView > .scrollbar--horizontal {
    background: #2d3748;
}

ScrollView > .scrollbar--corner {
    background: #2d3748;
}

/* Loading states */
.loading {
    color: #f6ad55;
    text-style: bold;
}

/* Progress indicators */
ProgressBar {
    background: #2d3748;
    color: #3182ce;
    border: solid #4a5568;
}

ProgressBar > .bar--complete {
    background: #38a169;
}

ProgressBar > .bar--indeterminate {
    background: #3182ce;
}
"""