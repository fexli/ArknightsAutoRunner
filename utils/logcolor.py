class Color(object):
    class print(object):
        class html(object):
            RED = "<font color='red' size='3'>"
            BOLD = "<font color='bold' size='3'>"
            BLUE = "<font color='blue' size='3'>"
            CYAN = "<font color='cyan' size='3'>"
            GREEN = "<font color='green' size='3'>"
            PURPLE = "<font color='purple' size='3'>"
            YELLOW = "<font color='yellow' size='3'>"
            BROWN = "<font color='brown' size='3'>"
            BLACK = "<font color='black' size='3'>"
            WHITE = "<font color='white' size='3'>"
            DARKCYAN = "<font color='darkcyan' size='3'>"
            BOLDGRAY = "<font color='gray' size='3'>"
            DARKRED = "<font color='darkred' size='3'>"
            DARKGRAY = "<font color='darkgray' size='3'>"
            DARKBLUE = "<font color='darkblue' size='3'>"
            DARKGREEN = "<font color='darkgreen' size='3'>"
            DARKPURPLE = "<font color='dark_purple' size='3'>"
            LIGHTGREEN = "<font color='lightgreen' size='3'>"
            UNDERLINE = "<u>"
            SOUND = "<font color='black' size='3'>"  # dengdengdeng
            END = '</font>'

        RED = '\033[91m'
        BOLD = '\033[1m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        PURPLE = '\033[95m'
        YELLOW = '\033[93m'
        BROWN = "\033[0;33m"
        BLACK = "\033[0;30m"
        WHITE = "\033[1;37m"
        DARKCYAN = '\033[36m'
        BOLDGRAY = "\033[1;30m"
        DARKRED = "\033[1;31m"
        DARKGRAY = "\033[0;37m"
        DARKBLUE = "\033[1;34m"
        DARKGREEN = "\033[1;32m"
        DARKPURPLE = "\033[1;35m"
        LIGHTGREEN = "\033[2;32m"
        UNDERLINE = '\033[4m'
        SOUND = '\007'  # dengdengdeng
        END = '\033[0m'
        list = ['RED', 'BOLD', 'BLUE', 'CYAN', 'GREEN', 'PURPLE', 'YELLOW', 'BROWN', 'BLACK', 'WHITE', 'DARKCYAN',
                'BOLDGRAY',
                'DARKRED', 'DARKGRAY', 'DARKBLUE', 'DARKGREEN', 'DARKPURPLE', 'LIGHTGREEN', 'UNDERLINE',
                'SOUND', 'END']

    def convert(self):
        digit = list(map(str, range(10)))
        if isinstance(self, tuple):
            string = '#'
            for i in self:
                v1 = 1 // 16
                v2 = i % 16
                string += digit[v1] + digit[v2]
            return string
        elif isinstance(self, str):
            a1 = int(self[1], 16) * 16 + int(self[2], 16)
            a2 = int(self[3], 16) * 16 + int(self[4], 16)
            a3 = int(self[5], 16) * 16 + int(self[6], 16)
            return a1, a2, a3
