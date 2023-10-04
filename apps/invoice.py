from datetime import datetime

from rich.console import Console
console = Console()


class InvoiceGenerator:
    def __init__(self, teams_data: dict):
        self.data = teams_data

    @staticmethod
    def _template(
        team_id: int,
        team_name: str,
        owners: list,
        member_count: int,
        bill_amount: int,
    ):
        def _owner_template(owners_: list):
            trunc_owners = [
                (value["owner_name"], value["owner_email"])
                for owner in owners_
                for value in owner.values()
            ]
            return "\n".join([f"|{owner[0]}|{owner[1]}|" for owner in trunc_owners])

        return f"""◆ **Team:** {team_name}                      ◇ **Team ID:** {team_id}

|Owner Name| Owner Email|
|:----------|------------:|
{_owner_template(owners)}
        
**Number of members:** {member_count}

**💲 Total amount due:** {member_count * bill_amount} EUR

---

"""

    def generate(self):
        invoice = f"""# Invoice

*Generated on:* {datetime.today().strftime("%Y-%m-%d")}

"""
        with console.status(status="Generating invoice..."):
            for team in self.data.values():
                team_id = team["team_id"]
                team_name = team["team_name"]
                owners = team["owners"]
                member_count = team["members"]["member_count"]
                bill_amount = 0 if team["on_trial"] else 8
                team_invoice = self._template(
                    team_id, team_name, owners, member_count, bill_amount
                )
                invoice += team_invoice
        return invoice
