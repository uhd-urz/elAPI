from datetime import datetime


class InvoiceGenerator:
    __slots__ = ("data",)

    def __init__(self, teams_data: dict):
        self.data = teams_data

    @property
    def MONTHLY_FEE(self) -> int:
        return 8

    @MONTHLY_FEE.setter
    def MONTHLY_FEE(self, value):
        raise AttributeError("MONTHLY_FEE cannot be modified!")

    @MONTHLY_FEE.deleter
    def MONTHLY_FEE(self):
        raise TypeError("MONTHLY_FEE cannot be deleted!")

    @staticmethod
    def _template(
        team_id: int,
        team_name: str,
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
        
**Number of members:** {member_count}

**💲 Amount due:** {member_count * bill_amount:.2f} EUR

---

"""

    @staticmethod
    def _header(total_teams_count: int, total_bill_amount: int):
        return f"""# Invoice

*Generated on: {datetime.today().strftime("%Y-%m-%d")}*

## Overview

```yaml
Total number of teams: {total_teams_count}
Total amount due: {total_bill_amount: .2f} EUR
```

"""

    def generate(self):
        total_bill_amount = 0
        breakdown = """## Breakdown

"""
        for team in self.data.values():
            team_id = team["team_id"]
            team_name = team["team_name"]
            member_count = team["active_member_count"]
            bill_amount = 0 if team["on_trial"] else self.MONTHLY_FEE
            total_bill_amount += bill_amount * member_count
            team_invoice = self._template(team_id, team_name, member_count, bill_amount)
            breakdown += team_invoice
        return self._header(len(self.data.values()), total_bill_amount) + breakdown
