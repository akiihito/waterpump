import ipywidgets as widgets


def run(a, b):
    print(f"Slider : {a}\nDropdown : {b}")

widgets.interact(
    run,
    a=widgets.IntSlider(
        value=1,
        min=1,
        max=3,
        step=1,
        description="Slider :",
    ),
    b=widgets.Dropdown(
        options=["1", "2", "3"],
        value="2",
        description="Dropdown :",
        disabled=False,
    ),
)