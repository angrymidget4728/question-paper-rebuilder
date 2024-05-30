import flet as ft
from flet import Page, Container, Column, Row, Text, Image
from builder_screen import BuilderScreen

class TabButton(Container):
    def __init__(self, tab_text):
        super().__init__(
            content=Text(tab_text, size=16),
            bgcolor=ft.colors.GREY,
            padding=ft.padding.symmetric(5,10),
            border_radius=5,
        )

class TabsRow(Row):
    def __init__(self, active_tab_index=0, screen_list: list = [], page: Page = None):
        super().__init__(
            controls=[
                TabButton("Builder"),
                TabButton("Splitter"),
            ]
        )
        self.active_tab_index = active_tab_index
        self.screen_list = screen_list
        self.page = page
        
        for tab in self.controls: tab.on_click = self.activate_tab

        self.controls[active_tab_index].bgcolor = ft.colors.BLUE
    
    def activate_tab(self, e: ft.TapEvent):
        if self.active_tab_index != self.controls.index(e.control):
            self.deactivate_tab()

            e.control.bgcolor = ft.colors.BLUE
            self.active_tab_index = self.controls.index(e.control)
            self.page.controls.append(self.screen_list[self.active_tab_index])
            self.page.update()

    def deactivate_tab(self):
        self.controls[self.active_tab_index].bgcolor = ft.colors.GREY
        self.page.controls.pop()
        self.update()


class SplitterScreen(Row):
    def __init__(self):
        super().__init__(
            controls=[
                Column(
                    controls=[
                        ft.SearchBar(), # Filters
                        Row(
                            controls=[
                                ft.GridView()
                            ],
                            expand=True,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        ), # Gallery
                        Row(
                            controls=[
                                Container(
                                    content=Text("Split Paper"),
                                    bgcolor=ft.colors.BLUE_400,
                                    padding=ft.padding.symmetric(5, 15),
                                    border_radius=100,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    expand=True,
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

def main(page: Page):
    page.bgcolor = ft.colors.GREY_900
    active_screen = 0
    screen_list = [BuilderScreen(), SplitterScreen()]
    page.add(
        TabsRow(active_screen, screen_list, page),
        screen_list[active_screen],
    )

if __name__ == "__main__":
    ft.app(target=main)