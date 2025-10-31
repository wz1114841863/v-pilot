import typer
from vpilot.commands import spec, plan, uvm

app = typer.Typer(help="v-pilot: Simulation Testing Assisted Generation Tool.")

app.add_typer(spec.app, name="spec")
# app.add_typer(plan.app, name="plan")
# app.add_typer(uvm.app, name="uvm")

if __name__ == "__main__":
    app()
