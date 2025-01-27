from tkinter import Tk, Listbox, Entry, Event, Scrollbar, Y, X, BOTH, RIGHT, \
        LEFT, BOTTOM
from typing import List
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


class Gui:
    # def searchChange(self, event: Event):
    #     value = event.widget.get()
    #     self.vals = self.spectrum.search_elements(value)
    #     self.update()

    def selectElem(self, event: Event):
        w = event.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        elem = self.vals[index]
        ts = self.spectrum.get_tests(elem.group, only_failing=True)
        print('You selected item %d: "%s" with failing tests: %s' % (index, elem, ts))

    def __init__(self, spectrum: Spectrum, all_sorts=List[List[Scores]]):
        # initialise root
        self.spectrum = spectrum
        root = Tk(className='flitsr')
        # add search bar
        # e = Entry(self.root)
        # e.pack()
        # e.bind('<KeyRelease>', self.searchChange)
        # add list with scrollbar
        yscrollbar = Scrollbar(root)
        xscrollbar = Scrollbar(root, orient='horizontal')
        yscrollbar.pack(side=RIGHT, fill=Y)
        xscrollbar.pack(side=BOTTOM, fill=X)
        self.lb = Listbox(root, yscrollcommand=yscrollbar.set,
                          xscrollcommand=xscrollbar.set)
        self.lb.bind('<<ListboxSelect>>', self.selectElem)
        self.lb.pack(side=LEFT, fill=BOTH, expand=True)
        yscrollbar.config(command=self.lb.yview)
        xscrollbar.config(command=self.lb.xview)
        # fill list
        self.vals: Scores = all_sorts[0][0]
        self.update()
        # mainloop
        root.mainloop()

    def update(self):
        self.lb.delete(0, 'end')
        scores = [s.score for s in self.vals]
        rng = [min(scores), max(scores)]
        for score in self.vals:
            self.lb.insert('end', score.group)
            # calculate colour based on score
            perc = (score.score - rng[0])/(rng[1] - rng[0])
            clr_num = (int(255*perc))*256**2 + (int(255*(1-perc)))*256
            clr = "#{0:06X}".format(clr_num)
            self.lb.itemconfig('end', {'bg': clr})
