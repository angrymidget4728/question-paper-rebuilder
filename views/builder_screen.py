import flet as ft, os
from flet import Container, Column, Row, Text, Image, Stack, Icon

_questions_path = "./exports/questions"
_question_ids_path = "./exports/question_ids"

class ImageBlock(Container):
    def __init__(self, image_path, on_click=None):
        super().__init__(
            content=Stack(
                controls=[
                    Image(
                        src=image_path,
                        border_radius=10,
                        fit=ft.ImageFit.COVER,
                        height=float('inf'),
                    ),
                    Container(
                        content=Icon(ft.icons.ZOOM_IN),
                        right=5,
                        bottom=5,
                        opacity=0,
                        on_hover=self._hover_action
                    )
                ],
            ),
            padding=5,
            # bgcolor=ft.colors.BLUE,
            on_click=on_click,
        )
    
    def _hover_action(self, e: ft.HoverEvent):
        if e.data == 'true':
            e.control.opacity = 1
        else:
            e.control.opacity = 0
        e.control.update()

    

class BuilderScreen(Row):
    def __init__(self, selected_items = []):
        super().__init__(
            controls=[
                Column(
                    controls=[
                        Row(
                            controls=[
                                ft.Dropdown(label="Curriculum & Grade", expand=True),
                                ft.Dropdown(label="Subject & Code", expand=True),
                                ft.Dropdown(label="Year", expand=True),
                                ft.Dropdown(label="Session & Variant", expand=True),
                                ft.Dropdown(label="Topic", expand=True),
                            ],
                        ), # Filters
                        Row(
                            controls=[
                                Container(
                                    content=ft.GridView(
                                        # expand=True,
                                        max_extent=200,
                                        child_aspect_ratio=1,
                                        spacing=5,
                                        run_spacing=5,
                                    ),
                                    expand=True,
                                    bgcolor=ft.colors.GREY_800,
                                    border_radius=10,
                                    padding=10,
                                ),
                            ],
                            expand=True,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        Row(
                            controls=[
                                Container(
                                    content=Text("Refresh"),
                                    bgcolor=ft.colors.BLUE_300,
                                    padding=ft.padding.symmetric(5, 15),
                                    border_radius=100,
                                    on_click=self._refresh_list,
                                ),
                                Container(
                                    content=Text("Build Paper"),
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

        # self(Row)/controls[0](Column)/controls[1](Row)/controls[0](Container)/content(GridView)/controls
        self.image_list = self.controls[0].controls[1].controls[0].content.controls
        self.selected_items = selected_items
        self._add_questions_to_grid()
    
    def _add_questions_to_grid(self):
        for filename in os.listdir(_questions_path):
            img_path = os.path.join(_questions_path, filename)
            if os.path.isfile(img_path):
                self.image_list.append(ImageBlock(
                    image_path=img_path,
                    on_click=self._toggle_selection,
                ))
    
    def _toggle_selection(self, e: ft.TapEvent):
        if e.control not in self.selected_items:
            e.control.bgcolor = ft.colors.BLUE
            self.selected_items.append(e.control)
            e.control.content.controls.append(
                Container(
                    bgcolor=ft.colors.BLUE,
                    content=Text(f"{len(self.selected_items)}"),
                    left=5,
                    bottom=5,
                    border_radius=5,
                    padding=5,
                )
            )
            e.control.update()
        else:
            clicked_item_index = self.selected_items.index(e.control)
            e.control.content.controls.pop()
            e.control.bgcolor = None
            self.selected_items.pop(clicked_item_index)
            for item in self.selected_items[clicked_item_index:]:
                item.content.controls[-1].content.value = str(int(item.content.controls[-1].content.value)-1)
            self.update()
    
    def _refresh_list(self, e: ft.TapEvent):
        self.image_list.clear()
        self.selected_items.clear()
        self._add_questions_to_grid()
        self.update()
    


