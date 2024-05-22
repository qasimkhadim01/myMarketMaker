import tkinter as tk

class Application():
    def __init__(self):
        root = tk.Tk()
        frameExecutions = tk.Frame(root)
        frameExecutions.grid()

        yScroll = tk.Scrollbar(frameExecutions, orient=tk.VERTICAL)
        yScroll.grid(row=0, column=1, sticky=tk.NW+tk.S)
        xScroll = tk.Scrollbar(frameExecutions, orient=tk.HORIZONTAL)
        xScroll.grid(row=1, column=0, sticky=tk.E+tk.W)
        self.listbox = tk.Listbox(frameExecutions, xscrollcommand=xScroll.set, yscrollcommand=yScroll.set)
        self.listbox.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        cities = ('CASTELL DE L''ARENY',
             'CASTELLADRAL',
             'CASTELLAR',
             'CASTELLAR DE N''HUG',
             'CASTELLAR DEL RIU',
             'CASTELLBELL I VILLAR',
             'CASTELLBISBAL',
             'CASTELLCIR',
             'CASTELLDEFELS',
             'CASTELLET',
             'CASTELLFOLLIT DE RIUBREGOS',
             'CASTELLFOLLIT DEL BOIX',
             'CASTELLGALI',
             'CASTELLNOU DE BAGES',
             'CASTELLOLI',
             'CASTELLTALLAT',
             'CASTELLTERÇOL',
             'CASTELLVI DE LA MARCA',
             'CASTELLVI DE ROSANES',
             'CENTELLES')
        self.listbox.insert(tk.END,*cities)
        xScroll['command'] = self.listbox.xview
        yScroll['command'] = self.listbox.yview

        frameExecutions.mainloop()

app = Application()

