
colors =  {
            'lightest':"#eeeeee",
            'lighter':"#e5e5e5",
            'light':"#effffb",
            'himid':"#50d890",
            'midmid':"#1089ff",
            'lomid':"#4f98ca",
            'dark' :"#272727",
            'darker' :"#23374d",
}


QPushButton_style = f"""
QPushButton{{
	color: {colors['light']};
	background-color: transparent;
	border: 1px solid #4589b2;
	padding: 5px;
}}
QPushButton::hover{{
	background-color: rgba(255,255,255,.2);
}}
QPushButton::pressed{{
	border: 1px solid {colors['himid']};
	background-color: rgba(0,0,0,.3);
}}"""
