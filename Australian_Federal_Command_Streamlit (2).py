import math
import random
import types
import streamlit as st

class _StateVar:
    def __init__(self, value=None): self._value = value
    def get(self): return self._value
    def set(self, value): self._value = value
    def trace_add(self, *args, **kwargs): return None

class _DummyWidget:
    def __init__(self, *args, **kwargs): self._exists=True; self.text=""; self.value=0; self.rows=[]; self._selection=[]
    def config(self, **kwargs):
        if "text" in kwargs: self.text=kwargs["text"]
        if "value" in kwargs: self.value=kwargs["value"]
        return None
    configure=config
    def winfo_exists(self): return self._exists
    def winfo_children(self): return []
    def destroy(self): self._exists=False
    def place_forget(self): return None
    def get_children(self): return list(range(len(self.rows)))
    def delete(self, item): return None
    def insert(self, *args, **kwargs): self.rows.append(kwargs.get("values", ())); return len(self.rows)-1
    def selection(self): return list(self._selection)
    def item(self, sel):
        i=sel[0] if isinstance(sel,(list,tuple)) else sel
        if isinstance(i,int) and i < len(self.rows): return {"values": self.rows[i]}
        return {"values": ()}

class _Root(_DummyWidget):
    def title(self, *args, **kwargs): return None
    def geometry(self, *args, **kwargs): return None
    def configure(self, *args, **kwargs): return None
    def after(self, *args, **kwargs): return None

class _TextWidget(_DummyWidget):
    def delete(self, *args, **kwargs): self.text=""
    def insert(self, *args, **kwargs):
        content = args[1] if len(args)>1 else kwargs.get("text", "")
        self.text += str(content)

class _Progress(_DummyWidget): pass

class _MessageBox:
    @staticmethod
    def _push(level, title, msg):
        st.session_state.setdefault("notifications", []).append((level, title, msg))
    @classmethod
    def showinfo(cls, title, msg): cls._push("info", title, msg)
    @classmethod
    def showwarning(cls, title, msg): cls._push("warning", title, msg)
    @classmethod
    def showerror(cls, title, msg): cls._push("error", title, msg)
    @staticmethod
    def askyesno(*args, **kwargs): raise RuntimeError("Synchronous confirmation was converted to a Streamlit confirmation action.")
    @staticmethod
    def askokcancel(*args, **kwargs): raise RuntimeError("Synchronous confirmation was converted to a Streamlit confirmation action.")
messagebox = _MessageBox
tk = types.SimpleNamespace(StringVar=_StateVar, DoubleVar=_StateVar, END="end", TclError=Exception)

class AustraliaBudgetGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Can You Save Australia's Budget & Economy?")
        self.root.geometry("1280x960")
        self.root.configure(bg="#F4F6F9")

        # --- Game Variables ---
        self.month = 1
        self.year = 2026
        self.term_month = 1
        self.total_months_played = 1
        self.term_count = 1

        self.events_this_term = 0
        self.max_events_this_term = 0 # No events first 12 months

        self.population = 26_500_000
        self.debt = 978.7
        self.in_election = False
        self.in_event = False
        self.bondi_event_occurred = False
        self.fuel_crisis_occurred = False
        self.oil_spill_prevented = False
        self.housing_crisis_blocked_until = 0
        self.net_zero_push_occurred = False
        self.net_zero_accepted = None
        self.black_market_occurred = False
        self.black_market_police_timer = 0
        self.shale_oil_occurred = False
        self.shale_boom_timer = 0
        self.shale_oil_penalty = 0.0
        self.ruling_party = "Labour"

        self.recession_active = False
        self.recession_recovery_timer = 0
        self.unemployment_event_occurred = False
        self.trade_war_event_occurred = False

        self.immigration_zero_months = 0
        self.bigot_event_occurred = False

        self.nuclear_sanctions = False
        self.pending_war_damage = []

        self.recent_news = []

        # Munition Tracking Charges
        self.air_munitions_uses = 0
        self.naval_munitions_uses = 0
        self.hypersonic_uses = 0
        self.anti_drone_uses = 0

        # Term Averages & Trackers
        self.term_happiness_history = []
        self.term_crime_history = []
        self.months_happy_over_75 = 0
        self.player_declared_wars_this_term = 0

        # Build Queue, Active Procurements & Locked Settings
        self.build_queue = []
        self.active_procurements = []  # Tracks procurement spending for acquire time + 6 months
        self.locked_settings = {}       # Tracks party demand locks (3 months duration)

        self.airbase_names = ['RAAF Amberley', 'RAAF Richmond', 'RAAF Darwin', 'RAAF Tindal', 'RAAF Williamtown', 'RAAF Pearce', 'RAAF Edinburgh', 'RAAF Townsville', 'RAAF Learmonth', 'RAAF Curtin', 'RAAF Scherger', 'RAAF East Sale', 'RAAF Base Wagga']

        # Defense Target Allocations
        self.facility_protections = {
            t: {"THAAD System": 0, "Patriot Battery": 0}
            for t in ["Oil Refinery", "LNG Processing Facility", "Offshore Oil Rig", "Coal Power Plant", "Nuclear Power Plant", "Advanced Fighter Jet Assembly", "Naval Submarine Base", "Upgraded Airbase", "Pine Gap Intelligence Base", "Zinc Refinery", "Nickel Refinery", "Tungsten Refinery"]
        }
        for airbase_name in self.airbase_names:
            self.facility_protections[airbase_name] = {"THAAD System": 0, "Patriot Battery": 0}

        self.tariffs_timer = 0
        self.tariffs_boost_active = False
        self.sanctions_active = False
        self.carbon_sanctions_active = False
        self.road_package_used_this_month = False

        # Event Modifiers
        self.event_happy_mod = 0.0
        self.event_crime_mod = 0.0
        self.event_health_mod = 0.0
        self.event_inflation_mod = 0.0
        self.event_unemployment_mod = 0.0
        self.net_zero_grid_penalty = 0.0

        # War Variables
        self.is_at_war = False
        self.war_opponent = ""
        self.war_duration = 0
        self.war_tier = 0
        self.defeated_countries = []
        self.ally_called_this_war = False
        self.ground_invasion_done = False

        self.senate_popularity = 50.0

        # Economic Stats
        self.inflation = 2.8
        self.cost_of_living = 100.0
        self.unemployment = 4.0
        self.health_index = 78.0
        self.crime_index = 32.0
        self.happiness = 72.0
        self.emissions = 45.0
        self.foreign_relations = 100.0
        self.power_bills = 120.0
        self.avg_interest_rate = 6.20
        self.property_price_index = 100.0
        self.investment_pullout_occurred = False
        self.interest_cap_override = None
        self.monthly_balance = 0.0
        self.structural_fixed_costs = 0.0

        self.last_month_stats = {"inflation": 2.8, "unemployment": 4.0, "happiness": 72.0}
        self.last_month_policies = {}

        self.immigration_policy = _StateVar(value="Moderate (35k/mo)")

        self.health_spend = _StateVar(value=8.5)
        self.police_spend = _StateVar(value=1.5)
        self.defence_spend = _StateVar(value=4.2)
        self.education_spend = _StateVar(value=4.0)
        self.infra_spend = _StateVar(value=2.0)
        self.housing_spend = _StateVar(value=0.5)
        self.foreign_aid = _StateVar(value=0.4)
        self.arts_funding = _StateVar(value=0.2)
        self.env_spend = _StateVar(value=0.3)

        # Climate Variables
        self.climate_spend = _StateVar(value=1.5)
        self.net_zero_spend = _StateVar(value=1.0)

        # Welfare Variables (Exact Dollar Rates for Age Pension and Family Tax Benefits)
        self.age_pension = _StateVar(value=1200.0)
        self.aged_care_cover = _StateVar(value=70.0)
        self.ndis_spend = _StateVar(value=3.5)
        self.jobseeker = _StateVar(value=1.2)
        self.family_benefits = _StateVar(value=300.0)

        self.tax_bracket_15 = _StateVar(value=15.0)
        self.tax_bracket_30 = _StateVar(value=30.0)
        self.tax_bracket_37 = _StateVar(value=37.0)
        self.tax_bracket_45 = _StateVar(value=45.0)
        self.company_tax_rate = _StateVar(value=30.0)
        self.small_business_tax = _StateVar(value=25.0)
        self.payroll_tax = _StateVar(value=5.0)
        self.gst_rate = _StateVar(value=10.0)
        self.super_tax_rate = _StateVar(value=15.0)
        self.fuel_excise_rate = _StateVar(value=53.7)
        self.cgt_rate = _StateVar(value=25.0)
        self.land_tax = _StateVar(value=1.5)
        self.sin_tax = _StateVar(value=65.0)

        # New Tax Options
        self.luxury_car_tax = _StateVar(value=33.0)
        self.annual_wealth_tax = _StateVar(value=0.0)
        self.medicare_levy = _StateVar(value=2.0)
        self.infrastructure_levy = _StateVar(value=0.0)
        self.fin_trans_tax = _StateVar(value=0.0)
        self.wage_cpi_index = _StateVar(value=0.0)

        # Tax Options
        self.negative_gearing = _StateVar(value=100.0)
        self.cgt_discount = _StateVar(value=50.0)
        self.fbt_rate = _StateVar(value=47.0)

        self.facilities = {
            "Oil Refinery": {"type": "Industry", "count": 1, "cost": 4.0, "rev": 0.45, "upkeep": 0.234, "workers": 8000, "build_time": 5},
            "Oil Extraction Field": {"type": "Industry", "count": 0, "cost": 25.0, "rev": 1.5, "upkeep": 0.4, "workers": 3000, "build_time": 8},
            "Offshore Oil Rig": {"type": "Industry", "count": 0, "cost": 6.5, "rev": 0.7, "upkeep": 0.351, "workers": 3000, "build_time": 3},
            "Iron Ore Smelter": {"type": "Industry", "count": 2, "cost": 5.0, "rev": 0.65, "upkeep": 0.292, "workers": 12000, "build_time": 4},
            "Gold Refinery": {"type": "Industry", "count": 1, "cost": 6.0, "rev": 0.75, "upkeep": 0.328, "workers": 5000, "build_time": 3},
            "Gas Field": {"type": "Industry", "count": 0, "cost": 15.0, "rev": 0.8, "upkeep": 0.3, "workers": 2000, "build_time": 5},
            "LNG Processing Facility": {"type": "Industry", "count": 2, "cost": 5.5, "rev": 0.6, "upkeep": 0.257, "workers": 9000, "build_time": 5},
            "Lithium Processing Plant": {"type": "Industry", "count": 0, "cost": 4.5, "rev": 0.5, "upkeep": 0.175, "workers": 6000, "build_time": 3},
            "Uranium Mine": {"type": "Industry", "count": 0, "cost": 3.0, "rev": 0.3, "upkeep": 0.1, "workers": 800, "build_time": 4},
            "Rare Earths Refinery": {"type": "Industry", "count": 0, "cost": 5.0, "rev": 0.55, "upkeep": 0.210, "workers": 5500, "build_time": 4},
            "Copper Smelting Plant": {"type": "Industry", "count": 0, "cost": 4.8, "rev": 0.52, "upkeep": 0.158, "workers": 7000, "build_time": 3},
            "Zirconium Refinery": {"type": "Industry", "count": 0, "cost": 3.5, "rev": 0.4, "upkeep": 0.150, "workers": 4000, "build_time": 5},
            "Zinc Refinery": {"type": "Industry", "count": 0, "cost": 3.0, "rev": 0.35, "upkeep": 0.1, "workers": 3500, "build_time": 4},
            "Nickel Refinery": {"type": "Industry", "count": 0, "cost": 4.0, "rev": 0.45, "upkeep": 0.15, "workers": 4500, "build_time": 4},
            "Tungsten Refinery": {"type": "Industry", "count": 0, "cost": 4.5, "rev": 0.5, "upkeep": 0.18, "workers": 5000, "build_time": 5},
            "RAM Production Plant": {"type": "Industry", "count": 0, "cost": 3.0, "rev": 0.2, "upkeep": 0.1, "workers": 1500, "build_time": 3},
            "Geothermal Energy Plant": {"type": "Energy", "count": 0, "cost": 8.0, "rev": 0.25, "upkeep": 0.120, "workers": 1200, "build_time": 6},
            "Solar Farm Grid": {"type": "Energy", "count": 0, "cost": 6.0, "rev": 0.15, "upkeep": 0.080, "workers": 900, "build_time": 2},
            "Hydrogen Fuel Facility": {"type": "Energy", "count": 0, "cost": 7.5, "rev": 0.30, "upkeep": 0.150, "workers": 2000, "build_time": 4},
            "Nuclear Power Plant": {"type": "Energy", "count": 0, "cost": 25.0, "rev": 0.5, "upkeep": 0.4, "workers": 1000, "build_time": 20},
            "Coal Power Plant": {"type": "Energy", "count": 0, "cost": 4.0, "rev": 0.3, "upkeep": 0.1, "workers": 600, "build_time": 4},
            "Open-Cycle Gas Plant": {"type": "Energy", "count": 0, "cost": 5.0, "rev": 0.2, "upkeep": 0.15, "workers": 300, "build_time": 3},
            "Combined Cycle Gas Plant": {"type": "Energy", "count": 0, "cost": 9.0, "rev": 0.4, "upkeep": 0.15, "workers": 300, "build_time": 3},
            "Flood-Catchment Plant": {"type": "Energy", "count": 0, "cost": 10.0, "rev": 0.09, "upkeep": 0.05, "workers": 200, "build_time": 4},
            "Desalination Plant": {"type": "Energy", "count": 0, "cost": 6.0, "rev": 0.0, "upkeep": 0.08, "workers": 150, "build_time": 5},
            "Data Center": {"type": "Energy", "count": 0, "cost": 3.5, "rev": 0.1, "upkeep": 0.1, "workers": 300, "build_time": 5},
            "Upgraded Airbase": {"type": "Defense", "count": 0, "cost": 3.0, "rev": 0.0, "upkeep": 0.234, "workers": 1200, "build_time": 2},
            "Pine Gap Intelligence Base": {"type": "Defense", "count": 1, "cost": 4.0, "rev": 0.0, "upkeep": 0.120, "workers": 500, "build_time": 3},
            "Weapon Manufacturing Plant": {"type": "Defense", "count": 0, "cost": 4.5, "rev": 0.25, "upkeep": 0.175, "workers": 4000, "build_time": 3},
            "Advanced Fighter Jet Assembly": {"type": "Defense", "count": 0, "cost": 8.0, "rev": 0.35, "upkeep": 0.351, "workers": 5000, "build_time": 5},
            "Naval Submarine Base": {"type": "Defense", "count": 0, "cost": 15.0, "rev": 0.0, "upkeep": 0.468, "workers": 2500, "build_time": 10},
            "Nuclear Submarine (x3)": {"type": "Defense", "count": 0, "cost": 35.0, "rev": 0.0, "upkeep": 1.500, "workers": 800, "build_time": 12},
            "B-52H Bomber Squadron Fleet": {"type": "Defense", "count": 0, "cost": 12.0, "rev": 0.0, "upkeep": 0.520, "workers": 1500, "build_time": 6},
            "F-15 Fighter Squadron": {"type": "Defense", "count": 0, "cost": 7.0, "rev": 0.0, "upkeep": 0.310, "workers": 1800, "build_time": 4},
            "Abrams Tank package(x15)": {"type": "Defense", "count": 0, "cost": 2.5, "rev": 0.0, "upkeep": 0.15, "workers": 800, "build_time": 2},
            "Bushmaster package (x30)": {"type": "Defense", "count": 0, "cost": 1.5, "rev": 0.0, "upkeep": 0.08, "workers": 600, "build_time": 1},
            "Air-Surface Munitions Package": {"type": "Defense", "count": 0, "cost": 1.0, "rev": 0.0, "upkeep": 0.040, "workers": 300, "build_time": 1},
            "Drone Manufacturing Plant": {"type": "Defense", "count": 0, "cost": 3.5, "rev": 0.15, "upkeep": 0.140, "workers": 2200, "build_time": 2},
            "Satellite Grid": {"type": "Defense", "count": 0, "cost": 10.0, "rev": 0.05, "upkeep": 0.380, "workers": 800, "build_time": 5},
            "Cyber Security Division": {"type": "Defense", "count": 0, "cost": 2.5, "rev": 0.0, "upkeep": 0.110, "workers": 1500, "build_time": 1},
            "Patriot Battery": {"type": "Defense", "count": 0, "cost": 2.0, "rev": 0.0, "upkeep": 0.05, "workers": 100, "build_time": 1},
            "THAAD System": {"type": "Defense", "count": 0, "cost": 5.0, "rev": 0.0, "upkeep": 0.15, "workers": 150, "build_time": 2},
            "Anti-Drone Package": {"type": "Defense", "count": 0, "cost": 1.5, "rev": 0.0, "upkeep": 0.03, "workers": 80, "build_time": 1},
            "Hobart Class Destroyer": {"type": "Defense", "count": 0, "cost": 3.0, "rev": 0.0, "upkeep": 0.15, "workers": 300, "build_time": 4},
            "Hunter Class Frigate": {"type": "Defense", "count": 0, "cost": 4.0, "rev": 0.0, "upkeep": 0.1, "workers": 250, "build_time": 4},
            "Mongami Frigate": {"type": "Defense", "count": 0, "cost": 1.0, "rev": 0.0, "upkeep": 0.05, "workers": 150, "build_time": 2},
            "Naval Munitions Package": {"type": "Defense", "count": 0, "cost": 1.0, "rev": 0.0, "upkeep": 0.02, "workers": 50, "build_time": 1},
            "Anti-Ship Hypersonic Missiles": {"type": "Defense", "count": 0, "cost": 2.0, "rev": 0.0, "upkeep": 0.05, "workers": 100, "build_time": 2},
            "Ballistic Missile Program": {"type": "Defense", "count": 0, "cost": 100.0, "rev": 0.0, "upkeep": 2.0, "workers": 2000, "build_time": 6},
            "Nuclear Program": {"type": "Defense", "count": 0, "cost": 200.0, "rev": 0.0, "upkeep": 5.0, "workers": 3000, "build_time": 12},
        }

        self.resource_levies = {
            "Crude Oil": _StateVar(value=5.0),
            "Petrol": _StateVar(value=0.0),
            "Diesel": _StateVar(value=0.0),
            "Iron (Raw Material)": _StateVar(value=8.0),
            "Steel": _StateVar(value=0.0),
            "Gold": _StateVar(value=10.0),
            "Lithium": _StateVar(value=9.0),
            "Rare Earths": _StateVar(value=7.0),
            "Copper": _StateVar(value=6.0),
            "Uranium": _StateVar(value=5.0),
            "Zirconium": _StateVar(value=0.0),
            "Zinc": _StateVar(value=0.0),
            "Nickel": _StateVar(value=0.0),
            "Tungsten": _StateVar(value=0.0),
            "Beef": _StateVar(value=0.0),
            "RAM (Req. Plant)": _StateVar(value=0.0)
        }

        self.tariffs = {
            "Energy & Natural Resources": _StateVar(value=5.0),
            "Machinery & Auto": _StateVar(value=2.5),
            "Consumer Goods": _StateVar(value=3.0),
            "Textiles": _StateVar(value=4.0),
            "Electronics": _StateVar(value=2.0),
            "Agricultural products": _StateVar(value=2.5),
        }

        self.laws = {
            "Medicare Expansion Act": {"passed": False, "cost": 1.2, "health_bonus": 8, "happy_bonus": 4, "align": ["Greens", "Labour"]},
            "Tough-On-Crime Reform": {"passed": False, "cost": 0.8, "crime_sub": 7, "happy_bonus": 2, "align": ["One Nation", "Liberal"]},
            "Ban E-Cigarettes & Vapes": {"passed": False, "cost": 0.1, "health_bonus": 5, "happy_bonus": -2, "crime_add": 10, "align": ["One Nation"]},
            "Under 16 Social Media Ban": {"passed": False, "cost": 0.3, "health_bonus": 4, "happy_bonus": -3, "align": ["One Nation", "Labour"]},
            "Universal Green Energy Mandate": {"passed": False, "cost": 2.0, "happy_bonus": 3, "align": ["Greens"]},
            "Superannuation Tax Increase": {"passed": False, "rev_add": 0.8, "happy_bonus": -3, "align": ["Greens", "Labour"]},
            "National Integrity Commission": {"passed": False, "cost": 0.5, "happy_bonus": 5, "align": ["Labour", "Greens", "Liberal"]},
            "Federal Rent Assistance Boost": {"passed": False, "cost": 2.0, "happy_bonus": 6, "align": ["Greens", "Labour"]},
            "Universal Basic Income Trial": {"passed": False, "cost": 15.0, "happy_bonus": 15, "align": ["Greens"]},
            "Aged Care Staff Wage Hike": {"passed": False, "cost": 1.8, "health_bonus": 6, "happy_bonus": 4, "align": ["Labour", "Greens"]},
            "Heavy Vehicle Road User Charge": {"passed": False, "rev_add": 0.6, "happy_bonus": -2, "align": ["Nationals"]},
            "Digital Platforms Revenue Mandate": {"passed": False, "rev_add": 0.4, "happy_bonus": 1, "align": ["Labour"]},
            "Immigrants 10 Years Before Welfare": {"passed": False, "cost": -3.5, "infl_mod": -2.0, "happy_bonus": 1, "align": ["One Nation"]},
            "Pass Hydrogen Bus Bill": {"passed": False, "infl_mod": -2.0, "happy_bonus": 2, "align": ["Greens", "Labour"]},

            "Abolish 18c": {"passed": False, "align": ["Liberal", "One Nation"]},
            "Legalise Free Speech": {"passed": False, "cost": 0.0, "happy_bonus": 2, "align": ["Liberal", "One Nation"]},
            "Interest Rate Cap Act": {"passed": False, "align": ["Labour", "Greens"]},

            "Defund Private Universities": {"passed": False, "infl_mod": -2.5, "align": ["Liberal", "Greens"]},
            "Free TAFE": {"passed": False, "happy_bonus": 8, "infl_mod": -1.5, "align": ["Labour", "Greens"]},
            "Automise Defence Infrastructure": {"passed": False, "infl_mod": -2.0, "align": ["Liberal", "Nationals"]},
            "Automise Refining Infrastructure": {"passed": False, "infl_mod": -2.0, "happy_bonus": 6, "align": ["Liberal", "Nationals"]},

            "Block Foreign Property Purchases": {"passed": False, "infl_mod": -1.5, "align": ["One Nation", "Greens"]},
            "Ban Renewable Projects in Daintree": {"passed": False, "happy_bonus": 3, "align": ["One Nation", "Nationals"]},
            "No GST on Domestic Solar Panels": {"passed": False, "rev_add": 1.5, "infl_mod": 0.5, "align": ["Greens"]},
            "Strip Councils of House Blocking": {"passed": False, "infl_mod": -3.0, "happy_bonus": 10, "rev_add": 2.0, "align": ["Liberal", "Labour"]},
            "Anti-Corruption & Lobbying Act": {"passed": False, "align": ["Greens", "Labour", "Liberal"]},
            "Dedicate 8% RAM to Gaming": {"passed": False, "happy_bonus": 10, "align": ["Labour"]},
            "ADF Domestic Dispatch Act": {"passed": False, "cost": 5.0, "crime_sub": 45, "align": ["One Nation", "Nationals"]},

            "Illigalise Santanism": {"passed": False, "crime_sub": 10, "happy_bonus": 15, "align": ["One Nation"]}
        }

        # Market Commodities Baseline Data (AUD)
        self.market_prices = {
            "Water": {"unit": "Litre ($/L)", "base": 0.003, "current": 0.003, "factors": "Normal"},
            "Crude Oil": {"unit": "Litre ($/L)", "base": 1.10, "current": 1.10, "factors": "Normal"},
            "Iron": {"unit": "Kg ($/Kg)", "base": 0.80, "current": 0.80, "factors": "Normal"},
            "Steel": {"unit": "Kg ($/Kg)", "base": 1.20, "current": 1.20, "factors": "Normal"},
            "Beef": {"unit": "Kg ($/Kg)", "base": 12.00, "current": 12.00, "factors": "Normal"},
            "Gold": {"unit": "Gram ($/g)", "base": 110.00, "current": 110.00, "factors": "Normal"},
            "Uranium": {"unit": "Kg ($/Kg)", "base": 180.00, "current": 180.00, "factors": "Normal"},
            "Lithium": {"unit": "Kg ($/Kg)", "base": 25.00, "current": 25.00, "factors": "Normal"},
            "Zinc": {"unit": "Kg ($/Kg)", "base": 4.00, "current": 4.00, "factors": "Normal"},
            "Nickel": {"unit": "Kg ($/Kg)", "base": 20.00, "current": 20.00, "factors": "Normal"},
            "Tungsten": {"unit": "Kg ($/Kg)", "base": 40.00, "current": 40.00, "factors": "Normal"},
            "Coal": {"unit": "Kg ($/Kg)", "base": 0.20, "current": 0.20, "factors": "Normal"},
            "LNG": {"unit": "Kg ($/Kg)", "base": 0.70, "current": 0.70, "factors": "Normal"},
            "Petrol": {"unit": "Litre ($/L)", "base": 2.00, "current": 2.00, "factors": "Normal"},
            "Diesel": {"unit": "Litre ($/L)", "base": 2.15, "current": 2.15, "factors": "Normal"},
            "Electricity": {"unit": "kWh (¢/kWh)", "base": 25.0, "current": 25.0, "factors": "Normal"},
            "RAM": {"unit": "GB Stick ($/GB)", "base": 12.00, "current": 12.00, "factors": "Normal"},
            "Copper": {"unit": "Kg ($/Kg)", "base": 14.00, "current": 14.00, "factors": "Normal"},
        }
        # Mid-2026 normalized base demand indices. 100% is the reference level; values differ by
        # how economically essential and widely consumed each commodity is in 2026.
        realistic_base_demand = {
            "Water": 100.0,
            "Crude Oil": 88.0,
            "Iron": 72.0,
            "Steel": 76.0,
            "Beef": 55.0,
            "Gold": 32.0,
            "Uranium": 8.0,
            "Lithium": 24.0,
            "Zinc": 39.0,
            "Nickel": 36.0,
            "Tungsten": 12.0,
            "Coal": 65.0,
            "LNG": 70.0,
            "Petrol": 92.0,
            "Diesel": 86.0,
            "Electricity": 100.0,
            "RAM": 58.0,
            "Copper": 68.0,
        }
        for comm, data in self.market_prices.items():
            data["base_demand"] = realistic_base_demand.get(comm, 50.0)
            data["demand"] = data["base_demand"]

        self.satanism_passed_count = 0
        self.satanism_assassination_timer = 0
        self.force_market_crash = False

        # Base private jobs setup (Need to pre-calculate effective welfare values for starting stats)
        eff_age_pension = self.age_pension.get() * (4.5 / 1200.0)
        eff_family_benefits = self.family_benefits.get() * (1.6 / 300.0)
        welfare_total = eff_age_pension + self.ndis_spend.get() + self.jobseeker.get() + eff_family_benefits

        public_spending = self.health_spend.get() + self.police_spend.get() + welfare_total + \
                          self.defence_spend.get() + self.education_spend.get() + self.infra_spend.get() + \
                          self.housing_spend.get() + self.foreign_aid.get() + \
                          self.arts_funding.get() + self.env_spend.get() + \
                          (self.climate_spend.get() / 12.0) + (self.net_zero_spend.get() / 12.0)

        total_fac_workers = sum(d["count"] * d["workers"] for d in self.facilities.values())
        labor_force = (self.population * 0.62) + 35000
        self.base_private_jobs = (labor_force * 0.96) - (int(public_spending * 12_000) + total_fac_workers)

        self.setup_ui()

        # Set default market prices perfectly equal to baseline before auto-calc kicks in
        for comm, data in self.market_prices.items():
            data["current"] = data["base"]
            data["factors"] = "Baseline Set"

        # Auto-Calibration
        self.recalculate_economy()
        self.structural_fixed_costs = self.monthly_balance + 2.5
        self.recalculate_economy()

        # Call party popup
        self.root.after(100, self.ask_party)

    def return_to_main_menu(self):
        st.session_state.clear()
        st.session_state["game_started"] = False
        st.session_state["game"] = AustraliaBudgetGame(_Root())
        st.session_state["notifications"] = []
    def ask_party(self):
        # Party selection is rendered natively by Streamlit in render_party_screen().
        self.in_event = False
    def setup_ui(self):
        # Streamlit owns the visual tree. These lightweight handles preserve the original
        # mechanics that update labels/trees during simulation calculations.
        self.lbl_balance = _DummyWidget(); self.lbl_debt = _DummyWidget(); self.lbl_interest = _DummyWidget()
        self.lbl_happiness = _DummyWidget(); self.lbl_unemp = _DummyWidget(); self.lbl_inflation = _DummyWidget(); self.lbl_date = _DummyWidget()
        self.prog_power = _Progress(); self.lbl_power = _DummyWidget()
        self.prog_foreign_rel = _Progress(); self.lbl_foreign_rel = _DummyWidget()
        self.prog_crime = _Progress(); self.lbl_crime = _DummyWidget()
        self.fac_tree = _DummyWidget(); self.war_status_lbl = _DummyWidget(); self.war_targets_frame = _DummyWidget()
        self.laws_frame = _DummyWidget(); self.market_tree = _DummyWidget(); self.news_text = _TextWidget()
        self.overlay_frame = _DummyWidget(); self.btn_next = _DummyWidget()
    def show_overlay(self, title_text, desc_text, color, buttons_data):
        self.in_event = True
        if not hasattr(self, 'recent_news'):
            self.recent_news = []
        if "ATTACK RESULT" not in title_text:
            self.recent_news.append(f"BREAKING: {title_text} - {desc_text.split('.')[0]}")
        st.session_state["overlay"] = {
            "title": title_text, "desc": desc_text, "color": color,
            "buttons": buttons_data,
        }
    def create_status_card(self, parent, title, initial_val):
        frame = tk.Frame(parent, bg="#003B63", bd=1, relief="solid")
        frame.pack(side="left", fill="both", expand=True, padx=4)
        t_lbl = tk.Label(frame, text=title, fg="#A0C4DF", bg="#003B63", font=("Helvetica", 9))
        t_lbl.pack(anchor="w", padx=5, pady=2)
        v_lbl = tk.Label(frame, text=initial_val, fg="white", bg="#003B63", font=("Helvetica", 12, "bold"))
        v_lbl.pack(anchor="w", padx=5, pady=2)
        return v_lbl

    def create_progress_card(self, parent, title, max_val):
        frame = tk.Frame(parent, bg="#003B63", bd=1, relief="solid")
        frame.pack(side="left", fill="both", expand=True, padx=4)
        t_lbl = tk.Label(frame, text=title, fg="#A0C4DF", bg="#003B63", font=("Helvetica", 10, "bold"))
        t_lbl.pack(anchor="w", padx=5, pady=2)

        inner_f = tk.Frame(frame, bg="#003B63")
        inner_f.pack(fill="x", padx=5, pady=2)

        prog = ttk.Progressbar(inner_f, orient="horizontal", length=250, mode="determinate", maximum=max_val)
        prog.pack(side="left", fill="x", expand=True)

        v_lbl = tk.Label(inner_f, text="", fg="white", bg="#003B63", font=("Helvetica", 11, "bold"), width=15)
        v_lbl.pack(side="right")
        return prog, v_lbl

    def setup_budget_tab(self):
        canvas = tk.Canvas(self.tab_budget, bg="#F4F6F9")
        scrollbar = ttk.Scrollbar(self.tab_budget, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#F4F6F9")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame_main = tk.LabelFrame(scrollable_frame, text=" MAIN FUNDING ($B $ / Month) ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        frame_main.pack(side="left", fill="both", expand=True, padx=8, pady=10)

        self.create_slider(frame_main, "Health & Medicare:", self.health_spend, 0.0, 30.0, is_currency=True)
        self.create_slider(frame_main, "Education & Universities:", self.education_spend, 0.0, 20.0, is_currency=True)
        self.create_slider(frame_main, "Housing Subsidies:", self.housing_spend, 0.0, 20.0, is_currency=True)
        self.create_slider(frame_main, "Police & National Security:", self.police_spend, 0.0, 15.0, is_currency=True)
        self.create_slider(frame_main, "Defence Forces:", self.defence_spend, 0.0, 20.0, is_currency=True)
        self.create_slider(frame_main, "Public Infrastructure:", self.infra_spend, 0.0, 18.0, is_currency=True)
        self.create_slider(frame_main, "Foreign Aid:", self.foreign_aid, 0.0, 10.0, is_currency=True)
        self.create_slider(frame_main, "Arts & Culture:", self.arts_funding, 0.0, 5.0, is_currency=True)
        self.create_slider(frame_main, "Environment Protection:", self.env_spend, 0.0, 8.0, is_currency=True)

        self.create_slider(frame_main, "Climate Change Funding:", self.climate_spend, 0.0, 13.0, is_currency=True)
        self.create_slider(frame_main, "Net Zero Funding:", self.net_zero_spend, 0.0, 12.0, is_currency=True)

        frame_welfare = tk.LabelFrame(scrollable_frame, text=" WELFARE ($ AUD / Month) ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        frame_welfare.pack(side="left", fill="both", expand=True, padx=8, pady=10)

        self.create_slider(frame_welfare, "Age Pension:", self.age_pension, 0.0, 3000.0, is_exact_dollars=True)
        self.create_slider(frame_welfare, "Aged Care Coverage:", self.aged_care_cover, 0.0, 100.0, is_percent=True)
        self.create_slider(frame_welfare, "NDIS (Disability Support):", self.ndis_spend, 0.0, 60.0, is_currency=True)
        self.create_slider(frame_welfare, "JobSeeker / Dole:", self.jobseeker, 0.0, 15.0, is_currency=True)
        self.create_slider(frame_welfare, "Family Tax Benefits:", self.family_benefits, 0.0, 1000.0, is_exact_dollars=True)

        frame_tax = tk.LabelFrame(scrollable_frame, text=" TAXATION (%) ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        frame_tax.pack(side="left", fill="both", expand=True, padx=8, pady=10)

        self.create_slider(frame_tax, "Inc. Tax ($18k-$45k):", self.tax_bracket_15, 0.0, 40.0, is_percent=True)
        self.create_slider(frame_tax, "Inc. Tax ($45k-$135k):", self.tax_bracket_30, 0.0, 50.0, is_percent=True)
        self.create_slider(frame_tax, "Inc. Tax ($134k-$190k):", self.tax_bracket_37, 0.0, 60.0, is_percent=True)
        self.create_slider(frame_tax, "Inc. Tax ($190k+):", self.tax_bracket_45, 0.0, 70.0, is_percent=True)
        self.create_slider(frame_tax, "Company Tax Rate:", self.company_tax_rate, 0.0, 40.0, is_percent=True)
        self.create_slider(frame_tax, "Small Business Tax:", self.small_business_tax, 0.0, 40.0, is_percent=True)
        self.create_slider(frame_tax, "Payroll Tax:", self.payroll_tax, 0.0, 15.0, is_percent=True)
        self.create_slider(frame_tax, "GST Rate:", self.gst_rate, 0.0, 25.0, is_percent=True)
        self.create_slider(frame_tax, "Super Tax Rate:", self.super_tax_rate, 0.0, 35.0, is_percent=True)
        self.create_slider(frame_tax, "Fuel Excise:", self.fuel_excise_rate, 0.0, 100.0, is_cents=True)
        self.create_slider(frame_tax, "Land Tax Rate:", self.land_tax, 0.0, 10.0, is_percent=True)
        self.create_slider(frame_tax, "Sin Tax (Alcohol/Tobacco):", self.sin_tax, 0.0, 150.0, is_percent=True)
        self.create_slider(frame_tax, "Negative Gearing (100=Full):", self.negative_gearing, 0.0, 100.0, is_percent=True)
        self.create_slider(frame_tax, "Capital Gains Discount:", self.cgt_discount, 0.0, 100.0, is_percent=True)
        self.create_slider(frame_tax, "Fringe Benefits Tax:", self.fbt_rate, 0.0, 100.0, is_percent=True)
        self.create_slider(frame_tax, "Medicare Levy:", self.medicare_levy, 0.0, 5.0, is_percent=True)
        self.create_slider(frame_tax, "Infrastructure Levy:", self.infrastructure_levy, 0.0, 5.0, is_percent=True)
        self.create_slider(frame_tax, "Luxury Car Tax:", self.luxury_car_tax, 0.0, 100.0, is_percent=True)
        self.create_slider(frame_tax, "Annual Wealth Tax:", self.annual_wealth_tax, 0.0, 10.0, is_percent=True)
        self.create_slider(frame_tax, "Financial Trans. Tax:", self.fin_trans_tax, 0.0, 5.0, is_percent=True)
        self.create_slider(frame_tax, "Wages vs CPI Index:", self.wage_cpi_index, -2.5, 2.5, is_percent=True)

    def create_slider(self, parent, label, var, from_, to, is_currency=False, is_percent=False, is_cents=False, is_exact_dollars=False):
        f = tk.Frame(parent, bg="#F4F6F9")
        f.pack(fill="x", pady=5, padx=5)
        lbl = tk.Label(f, text=label, bg="#F4F6F9", fg="black", font=("Helvetica", 10, "bold"), width=24, anchor="w")
        lbl.pack(side="left")

        val_str = _StateVar()

        def update_display(*args):
            val = var.get()
            if is_currency: val_str.set(f"${val:.1f}B AUD")
            elif is_exact_dollars: val_str.set(f"${val:.0f} / mo")
            elif is_percent: val_str.set(f"{val:.1f}%")
            elif is_cents: val_str.set(f"{val:.1f}¢ / L AUD")
            else: val_str.set(f"{val:.1f}")

        var.trace_add("write", update_display)
        update_display()

        scale = ttk.Scale(f, from_=from_, to=to, variable=var, command=lambda e: self.recalculate_economy())
        scale.pack(side="left", fill="x", expand=True, padx=5)

        val_lbl = tk.Label(f, textvariable=val_str, bg="#F4F6F9", fg="black", font=("Helvetica", 10, "bold"), width=14, anchor="e")
        val_lbl.pack(side="right")

    def setup_facilities_tab(self):
        self.fac_tree = ttk.Treeview(self.tab_facilities, columns=("Name", "Type", "Owned", "Cost", "Upkeep", "Rev", "Jobs"), show="headings")
        self.fac_tree.heading("Name", text="Facility Name")
        self.fac_tree.heading("Type", text="Sector Type")
        self.fac_tree.heading("Owned", text="Active Count")
        self.fac_tree.heading("Cost", text="Build Cost ($B AUD)")
        self.fac_tree.heading("Upkeep", text="Upkeep ($B AUD/mo)")
        self.fac_tree.heading("Rev", text="Revenue ($B AUD/mo)")
        self.fac_tree.heading("Jobs", text="Workers Needed")

        self.fac_tree.column("Name", width=220)
        self.fac_tree.column("Type", width=100)
        self.fac_tree.pack(fill="both", expand=True, padx=15, pady=5)

        btn_frame = tk.Frame(self.tab_facilities, bg="#F4F6F9")
        btn_frame.pack(fill="x", padx=15, pady=10)

        btn_build = tk.Button(btn_frame, text="BUILD SELECTED FACILITY", bg="#002B49", fg="#FFC72C",
                              font=("Helvetica", 11, "bold"), command=self.build_facility)
        btn_build.pack(side="left", padx=5)

        btn_abolish = tk.Button(btn_frame, text="ABOLISH SELECTED FACILITY", bg="#D9381E", fg="black",
                              font=("Helvetica", 11, "bold"), command=self.abolish_facility)
        btn_abolish.pack(side="left", padx=5)

        btn_road = tk.Button(btn_frame, text="FUND $2B ROAD PACKAGE", bg="#00843D", fg="black",
                              font=("Helvetica", 11, "bold"), command=self.enact_road_package)
        btn_road.pack(side="left", padx=5)

        self.update_facilities_table()

    def enact_road_package(self):
        if getattr(self, 'road_package_used_this_month', False):
            messagebox.showwarning("Limit Reached", "You can only fund the Road Package once per month!")
            return
        self.debt += 2.0
        self.event_happy_mod += 8.0
        self.event_inflation_mod += 2.0
        self.road_package_used_this_month = True
        messagebox.showinfo("Road Package Funded", "You have invested $2B AUD into a major Road Package.\nHappiness boosted by 8%, Inflation increased by 2%.")
        self.recalculate_economy()

    def update_facilities_table(self):
        for i in self.fac_tree.get_children():
            self.fac_tree.delete(i)
        labor_tightness = max(0.8, 1.2 - (self.unemployment - 3.5) * 0.05)
        for name, data in self.facilities.items():
            if name == "Pine Gap Intelligence Base":
                continue
            adj_upkeep = round(data["upkeep"] * labor_tightness, 3)
            adj_cost = data["cost"]
            if name == "Anti-Ship Hypersonic Missiles":
                zircon_ref_count = self.facilities["Zirconium Refinery"]["count"]
                discount = min(0.25, zircon_ref_count * 0.05)
                adj_cost = round(data["cost"] * (1.0 - discount), 2)
            building_count = sum(1 for b in self.build_queue if b["name"] == name)
            owned_str = f"{data['count']}" + (f" (+{building_count} Building)" if building_count > 0 else "")
            self.fac_tree.insert("", "end", values=(
                name, data["type"], owned_str, f"${adj_cost}B AUD", f"${adj_upkeep}B AUD", f"${data['rev']}B AUD", f"{data['workers']:,}"
            ))

    def build_facility(self):
        selected = self.fac_tree.selection()
        if not selected:
            return
        item = self.fac_tree.item(selected[0])
        fac_name = item["values"][0]
        if fac_name == "Pine Gap Intelligence Base": return
        if fac_name == "Upgraded Airbase":
            building_count = sum(1 for b in self.build_queue if b["name"] == fac_name)
            if self.facilities[fac_name]["count"] + building_count >= 13:
                messagebox.showerror("Limit Reached", "All airbases upgraded (Maximum 13).")
                return
        if fac_name == "LNG Processing Facility" and self.facilities["Gas Field"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build a $15B Gas Field before constructing an LNG Processing Facility."); return
        if fac_name == "Oil Refinery" and self.facilities["Oil Extraction Field"]["count"] == 0 and self.facilities["Offshore Oil Rig"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build an Oil Extraction Field or an Offshore Oil Rig before constructing an Oil Refinery."); return
        if fac_name == "Nuclear Submarine (x3)" and self.facilities["Naval Submarine Base"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build a Naval Submarine Base before acquiring a Nuclear Submarine."); return
        if fac_name in ["Abrams Tank package(x15)", "Bushmaster package (x30)"] and self.facilities["Weapon Manufacturing Plant"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build a Weapon Manufacturing Plant before acquiring land vehicles."); return
        if fac_name in ["F-15 Fighter Squadron", "B-52H Bomber Squadron Fleet"] and self.facilities["Advanced Fighter Jet Assembly"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build an Advanced Fighter Jet Assembly before acquiring these aircraft."); return
        if fac_name in ["Nuclear Power Plant", "Nuclear Program"] and self.facilities["Uranium Mine"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must build a Uranium Mine before pursuing nuclear capabilities."); return
        if fac_name in ["Ballistic Missile Program", "Nuclear Program"]:
            building_count = sum(1 for b in self.build_queue if b["name"] == fac_name)
            if self.facilities[fac_name]["count"] + building_count >= 1:
                messagebox.showerror("Limit Reached", f"You can only build 1 {fac_name}!"); return
        if fac_name == "Nuclear Program" and self.facilities["Ballistic Missile Program"]["count"] == 0:
            messagebox.showerror("Requirement Missing", "You must complete the Ballistic Missile Program before acquiring Nuclear Weapons."); return
        cost = self.facilities[fac_name]["cost"]
        if fac_name == "Anti-Ship Hypersonic Missiles":
            zircon_ref_count = self.facilities["Zirconium Refinery"]["count"]
            discount = min(0.25, zircon_ref_count * 0.05); cost = round(cost * (1.0 - discount), 2)
        build_time = self.facilities[fac_name]["build_time"]
        st.session_state["pending_build"] = {"name": fac_name, "cost": cost, "build_time": build_time, "target": None}
        st.session_state["confirmation"] = {
            "title": "Confirm Construction",
            "message": f"Commence building 1 x {fac_name} for ${cost:.2f}B AUD?\nIt will take {build_time} months to complete.",
            "action": "confirm_build",
        }
    def abolish_facility(self):
        selected = self.fac_tree.selection()
        if not selected: return
        fac_name = self.fac_tree.item(selected[0])["values"][0]
        if self.facilities[fac_name]["count"] > 0:
            cost = self.facilities[fac_name]["cost"]
            if fac_name == "Anti-Ship Hypersonic Missiles":
                zircon_ref_count = self.facilities["Zirconium Refinery"]["count"]; discount = min(0.25, zircon_ref_count * 0.05); cost = round(cost * (1.0 - discount), 2)
            refund = cost * 0.8
            st.session_state["pending_abolish"] = {"name": fac_name, "refund": refund}
            st.session_state["confirmation"] = {"title": "Confirm Abolish", "message": f"Are you sure you want to abolish 1 x {fac_name}?\nYou will receive 80% of its initial build cost (${refund:.2f}B AUD) instantly back into the budget.", "action": "confirm_abolish"}
        else:
            messagebox.showwarning("Cannot Abolish", f"You do not possess any active {fac_name} structures to abolish!")
    def setup_war_tab(self):
        canvas = tk.Canvas(self.tab_war, bg="#F4F6F9")
        scrollbar = ttk.Scrollbar(self.tab_war, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#F4F6F9")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        lbl = tk.Label(scrollable_frame, text="Global Conflict & Military Command", bg="#F4F6F9", fg="black", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=10)

        self.war_status_lbl = tk.Label(scrollable_frame, text="Status: PEACE", fg="black", bg="#F4F6F9", font=("Helvetica", 12, "bold"))
        self.war_status_lbl.pack(pady=5)

        self.war_targets_frame = tk.Frame(scrollable_frame, bg="#F4F6F9")
        self.war_targets_frame.pack(fill="x", expand=True, padx=20, pady=10)

        self.render_war_targets()

    def render_war_targets(self):
        for widget in self.war_targets_frame.winfo_children():
            widget.destroy()

        targets = [
            ("Low Power Status Nations", 1, ["PNG", "Fiji", "New Zealand", "Solomon Islands"]),
            ("Medium Power Status Nations", 2, ["Philippines", "Japan", "Taiwan", "Indonesia"]),
            ("Large Power Status Nations", 3, ["United States", "Russia", "China", "India"])
        ]

        for cat_name, tier, nations in targets:
            lf = tk.LabelFrame(self.war_targets_frame, text=f" {cat_name} ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
            lf.pack(fill="x", pady=10)
            for nation in nations:
                if nation in self.defeated_countries:
                    btn = tk.Button(lf, text=f"Declare War on {nation}", bg="#AAAAAA", fg="black",
                                    font=("Helvetica", 10, "bold", "overstrike"), state="disabled")
                else:
                    btn = tk.Button(lf, text=f"Declare War on {nation}", bg="#D9381E", fg="black",
                                    font=("Helvetica", 10, "bold"),
                                    command=lambda n=nation, t=tier: self.declare_war(n, t))
                btn.pack(side="left", padx=15, pady=15)

        self.war_commands_frame = tk.LabelFrame(self.war_targets_frame, text=" Active War Commands & Strikes ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        self.war_commands_frame.pack(fill="x", pady=20)

        attacks = [
            ("Air Strike ($1.0B)", 1.0, self.req_air_strike, "Requires F-15 or B-52H AND Air-Surface Munitions.", "Air Strike"),
            ("Missile Barrage ($2.0B)", 2.0, self.req_missile_barrage, "Requires Air-Surface or Naval Munitions.", "Missile Barrage"),
            ("Drone Barrage ($100M)", 0.1, self.req_drone_barrage, "Requires Drone Manufacturing Plant.", "Drone Barrage"),
            ("Cyber Attack ($100M)", 0.1, self.req_cyber_attack, "Requires Cyber Security Division.", "Cyber Attack"),
            ("Naval Strike ($2.0B)", 2.0, self.req_naval_strike, "Requires a Warship (Hobart/Hunter/Mongami) AND Naval Munitions.", "Naval Strike"),
            ("Submarine Strike ($2.0B)", 2.0, self.req_submarine_strike, "Requires Submarine/Naval Base AND Naval Munitions.", "Submarine Strike"),
            ("Conventional Ballistic Strike ($5.0B)", 5.0, self.req_ballistic_strike, "Requires Ballistic Missile Program.", "Conventional Ballistic Strike"),
            ("Nuclear Sub Strike ($50.0B)", 50.0, self.req_nuke_sub_strike, "Requires Nuclear Submarine AND Nuclear Program.", "Nuclear Sub Strike"),
            ("Nuclear Strike ($100.0B)", 100.0, self.req_nuclear_strike, "Requires Nuclear Program.", "Nuclear Strike"),
            ("Ground Invasion ($3.0B)", 3.0, self.req_ground_invasion, "Requires Abrams Tank AND Bushmaster.", "Ground Invasion")
        ]

        row, col = 0, 0
        for text, cost, req_fn, req_msg, atk_name in attacks:
            btn = tk.Button(self.war_commands_frame, text=text, bg="#002B49", fg="black", font=("Helvetica", 10, "bold"),
                            command=lambda n=atk_name, c=cost, rf=req_fn, rm=req_msg: self.execute_player_attack(n, c, rf, rm))
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            col += 1
            if col > 3:
                col = 0
                row += 1

    def req_air_strike(self):
        return (self.facilities["F-15 Fighter Squadron"]["count"] > 0 or self.facilities["B-52H Bomber Squadron Fleet"]["count"] > 0) and self.facilities["Air-Surface Munitions Package"]["count"] > 0
    def req_missile_barrage(self):
        return self.facilities["Air-Surface Munitions Package"]["count"] > 0 or self.facilities["Naval Munitions Package"]["count"] > 0 or self.facilities["Anti-Ship Hypersonic Missiles"]["count"] > 0
    def req_drone_barrage(self):
        return self.facilities["Drone Manufacturing Plant"]["count"] > 0
    def req_cyber_attack(self):
        return self.facilities["Cyber Security Division"]["count"] > 0
    def req_naval_strike(self):
        has_ship = self.facilities["Hobart Class Destroyer"]["count"] > 0 or self.facilities["Hunter Class Frigate"]["count"] > 0 or self.facilities["Mongami Frigate"]["count"] > 0
        return has_ship and (self.facilities["Naval Munitions Package"]["count"] > 0 or self.facilities["Anti-Ship Hypersonic Missiles"]["count"] > 0)
    def req_submarine_strike(self):
        return (self.facilities["Naval Submarine Base"]["count"] > 0 or self.facilities["Nuclear Submarine (x3)"]["count"] > 0) and self.facilities["Naval Munitions Package"]["count"] > 0
    def req_nuke_sub_strike(self):
        return self.facilities["Nuclear Submarine (x3)"]["count"] > 0 and self.facilities["Nuclear Program"]["count"] > 0
    def req_ballistic_strike(self):
        return self.facilities["Ballistic Missile Program"]["count"] > 0
    def req_nuclear_strike(self):
        return self.facilities["Nuclear Program"]["count"] > 0
    def req_ground_invasion(self):
        return self.facilities["Abrams Tank package(x15)"]["count"] > 0 and self.facilities["Bushmaster package (x30)"]["count"] > 0

    def execute_player_attack(self, attack_name, cost, req_fn, req_msg):
        if not self.is_at_war:
            messagebox.showwarning("Not At War", "You must be at war to use military strikes.")
            return
        if not req_fn():
            messagebox.showerror("Missing Requirements", req_msg)
            return

        if attack_name == "Ground Invasion":
            self.debt += cost
            self.ground_invasion_done = True
            self.event_happy_mod += 5.0
            msg = f"SUCCESS!\n\nYour ground forces have successfully launched the invasion to annex {self.war_opponent}!"
            if not hasattr(self, 'recent_news'): self.recent_news = []
            self.recent_news.append(f"Military Command: Australian troops launch major ground invasion of {self.war_opponent}.")
            self.show_overlay("INVASION LAUNCHED", msg, "#002B49", [("Continue", lambda: None, "#CCCCCC")])
            return

        def select_target(tgt):
            self.debt += cost
            if tgt == "Cities":
                self.foreign_relations = 0.0

            if attack_name == "Air Strike":
                self.air_munitions_uses += 1
                if self.air_munitions_uses >= 2:
                    self.facilities["Air-Surface Munitions Package"]["count"] -= 1
                    self.air_munitions_uses = 0
                    messagebox.showwarning("Munitions Depleted", "An Air-Surface Munitions Package was completely used up!")
            elif attack_name in ["Naval Strike", "Submarine Strike"]:
                if self.facilities["Naval Munitions Package"]["count"] > 0:
                    self.naval_munitions_uses += 1
                    if self.naval_munitions_uses >= 2:
                        self.facilities["Naval Munitions Package"]["count"] -= 1
                        self.naval_munitions_uses = 0
                        messagebox.showwarning("Munitions Depleted", "A Naval Munitions Package was completely used up!")
                elif self.facilities["Anti-Ship Hypersonic Missiles"]["count"] > 0:
                    self.hypersonic_uses += 1
                    if self.hypersonic_uses >= 3:
                        self.facilities["Anti-Ship Hypersonic Missiles"]["count"] -= 1
                        self.hypersonic_uses = 0
                        messagebox.showwarning("Munitions Depleted", "Anti-Ship Hypersonic Missiles were completely used up!")
            elif attack_name == "Missile Barrage":
                if self.facilities["Air-Surface Munitions Package"]["count"] > 0:
                    self.air_munitions_uses += 1
                    if self.air_munitions_uses >= 2:
                        self.facilities["Air-Surface Munitions Package"]["count"] -= 1
                        self.air_munitions_uses = 0
                        messagebox.showwarning("Munitions Depleted", "An Air-Surface Munitions Package was completely used up!")
                elif self.facilities["Naval Munitions Package"]["count"] > 0:
                    self.naval_munitions_uses += 1
                    if self.naval_munitions_uses >= 2:
                        self.facilities["Naval Munitions Package"]["count"] -= 1
                        self.naval_munitions_uses = 0
                        messagebox.showwarning("Munitions Depleted", "A Naval Munitions Package was completely used up!")
                elif self.facilities["Anti-Ship Hypersonic Missiles"]["count"] > 0:
                    self.hypersonic_uses += 1
                    if self.hypersonic_uses >= 3:
                        self.facilities["Anti-Ship Hypersonic Missiles"]["count"] -= 1
                        self.hypersonic_uses = 0
                        messagebox.showwarning("Munitions Depleted", "Anti-Ship Hypersonic Missiles were completely used up!")

            self.update_facilities_table()

            success_chance = max(0.1, 1.0 - (self.war_tier * 0.25))
            if attack_name in ["Nuclear Strike", "Nuclear Sub Strike"]: success_chance = 1.0

            if attack_name in ["Nuclear Strike", "Nuclear Sub Strike"] and self.war_opponent in ["Russia", "China", "United States"]:
                self.event_happy_mod -= 30.0
                msg = "NUCLEAR RETALIATION!\n\nYou struck a nuclear-armed superpower! They retaliated with their own nuclear arsenal, devastating Australian cities. Public morale is permanently destroyed."
            elif random.random() < success_chance:
                msg = f"SUCCESS!\n\nYour {attack_name} successfully devastated the enemy's {tgt}!"
            else:
                msg = f"INTERCEPTED!\n\nYour {attack_name} was intercepted by enemy defenses. The attack failed."

            if not hasattr(self, 'recent_news'): self.recent_news = []
            self.recent_news.append(f"Military Command: Australian forces execute {attack_name} against enemy {tgt}.")

            self.show_overlay("ATTACK RESULT", msg, "#002B49", [("Continue", lambda: None, "#CCCCCC")])

        self.show_overlay(
            f"SELECT TARGET FOR {attack_name.upper()}",
            f"Cost: ${cost}B AUD. Select enemy infrastructure to target. WARNING: Targeting Cities sets Foreign Relations to 0%!",
            "#8B0000",
            [
                ("Airbases", lambda: select_target("Airbases"), "#333333"),
                ("Navy Bases", lambda: select_target("Navy Bases"), "#333333"),
                ("Manufacturing Plants", lambda: select_target("Manufacturing Plants"), "#333333"),
                ("Energy Infrastructure", lambda: select_target("Energy Infrastructure"), "#333333"),
                ("Cities (WAR CRIME)", lambda: select_target("Cities"), "#D9381E"),
                ("Cancel", lambda: None, "#CCCCCC")
            ]
        )

    def declare_war(self, target, tier):
        if self.is_at_war:
            messagebox.showwarning("Already at War!", f"You are already fighting {self.war_opponent}!")
            return
        st.session_state["pending_war_declaration"] = {"target": target, "tier": tier}
        st.session_state["confirmation"] = {
            "title": "Confirm Declaration",
            "message": f"Are you sure you want to declare war on {target}?\n\nWARNING: The economy will crash during war! Missiles may destroy infrastructure!",
            "action": "confirm_war",
        }
    def update_war_ui(self):
        if self.is_at_war:
            self.war_status_lbl.config(text=f"Status: AT WAR with {self.war_opponent} ({self.war_duration} months remaining)", fg="black")
        else:
            self.war_status_lbl.config(text="Status: PEACE", fg="black")

    def trigger_invasion(self, attacker, tier):
        self.is_at_war = True
        self.war_opponent = attacker
        self.war_tier = tier
        self.war_duration = random.randint(12, 30)
        self.ally_called_this_war = False
        self.ground_invasion_done = False
        self.update_war_ui()
        self.recalculate_economy()
        self.update_facilities_table()

        self.show_overlay(
            "INVASION!",
            f"{attacker} has begun invading Australia due to weak national security (or targeted tariffs)!\nExpect missile strikes on your infrastructure.",
            "#8B0000",
            [("Acknowledge", lambda: None, "#CCCCCC")]
        )

    def calculate_military_score(self):
        air = self.facilities["F-15 Fighter Squadron"]["count"] * 2 + self.facilities["Advanced Fighter Jet Assembly"]["count"] * 3
        navy = self.facilities["Naval Submarine Base"]["count"] * 5
        drones = self.facilities["Drone Manufacturing Plant"]["count"] * 1.5 + self.facilities["Anti-Drone Package"]["count"]
        cyber = self.facilities["Cyber Security Division"]["count"] * 2
        missile = self.facilities["Patriot Battery"]["count"] * 2 + self.facilities["THAAD System"]["count"] * 4
        energy_indep = self.facilities["Oil Refinery"]["count"] + self.facilities["Nuclear Power Plant"]["count"]
        manpower = (self.population / 10_000_000) + self.defence_spend.get()
        return air + navy + drones + cyber + missile + energy_indep + manpower

    def resolve_war(self):
        enemy_scores = {1: 10, 2: 25, 3: 50}
        my_score = self.calculate_military_score()
        enemy_score = enemy_scores.get(self.war_tier, 20) + random.uniform(-5, 5)

        if self.war_tier == 3:
            def_capital = sum(data["cost"] * data["count"] for name, data in self.facilities.items() if data["type"] == "Defense")
            warships = self.facilities["Hobart Class Destroyer"]["count"] + self.facilities["Hunter Class Frigate"]["count"] + self.facilities["Mongami Frigate"]["count"]
            missile_spend = (self.facilities["Patriot Battery"]["count"] * 2.0 +
                             self.facilities["THAAD System"]["count"] * 5.0 +
                             self.facilities["Anti-Ship Hypersonic Missiles"]["count"] * 2.0 +
                             self.facilities["Ballistic Missile Program"]["count"] * 100.0 +
                             self.facilities["Nuclear Program"]["count"] * 200.0)
            plants = self.facilities["Weapon Manufacturing Plant"]["count"] + self.facilities["Advanced Fighter Jet Assembly"]["count"] + self.facilities["Drone Manufacturing Plant"]["count"]

            if def_capital < 250.0 or self.defence_spend.get() < 8.0 or plants < 2 or warships < 5 or missile_spend < 20.0:
                my_score = 0

        if my_score > enemy_score * 1.2:
            result = "WIN"
        elif my_score > enemy_score * 0.8:
            result = "STALEMATE"
        else:
            result = "LOSS"

        msg = ""
        if result == "WIN":
            annex_str = f" and you successfully annexed {self.war_opponent}" if self.ground_invasion_done else ""
            msg = f"Australia has emerged victorious against {self.war_opponent}!\n\nYour superior combined military forces secured the nation{annex_str}. Minimal infrastructure damage taken."
            self.debt -= (200.0 * self.war_tier)
            self.population += (2_500_000 * self.war_tier)
            if self.war_opponent not in self.defeated_countries:
                self.defeated_countries.append(self.war_opponent)
        elif result == "STALEMATE":
            msg = f"The war with {self.war_opponent} ended in a brutal stalemate.\n\nBoth sides sustained heavy damage. You survived, but at great cost."
            self.debt += (100.0 * self.war_tier)
        else:
            msg = f"Australia has been COMPLETELY DEFEATED by {self.war_opponent}!\n\nYour military forces were utterly overwhelmed. GAME OVER."

        def on_war_resolve():
            if result == "LOSS":
                self.return_to_main_menu()
                return

            def after_repair():
                self.is_at_war = False
                self.war_opponent = ""
                self.render_war_targets()
                self.update_war_ui()
                self.update_facilities_table()
                self.recalculate_economy()

            if hasattr(self, 'pending_war_damage') and self.pending_war_damage:
                self.prompt_war_repairs(after_repair)
            else:
                after_repair()

        self.show_overlay("WAR CONCLUDED", msg, "#002B49" if result=="WIN" else "#8B0000", [("Continue", on_war_resolve, "#FFFFFF")])

    def prompt_war_repairs(self, callback):
        repair_cost = sum(self.facilities[fac]["cost"] * 0.5 for fac in self.pending_war_damage)

        def repair_all():
            self.debt += repair_cost
            for fac in self.pending_war_damage:
                self.facilities[fac]["count"] += 1
            self.pending_war_damage.clear()
            self.update_facilities_table()
            callback()

        def abandon_all():
            self.pending_war_damage.clear()
            self.update_facilities_table()
            callback()

        lost_str = "\n".join([f"- {f} (${self.facilities[f]['cost']*0.5:.1f}B to repair)" for f in self.pending_war_damage])

        self.show_overlay("POST-WAR RECONSTRUCTION",
            f"The war is over, but infrastructure was heavily damaged:\n{lost_str}\n\nDo you want to fund repairs for a total of ${repair_cost:.1f}B AUD, or abandon them?",
            "#002B49",
            [
                (f"Fund Repairs (${repair_cost:.1f}B AUD)", repair_all, "#00843D"),
                ("Abandon Infrastructure", abandon_all, "#D9381E")
            ]
        )

    def trigger_enemy_war_event(self):
        events = ["Missile Barrage", "Navy Attack", "Airstrike", "Grid Sabotage", "Drone Attack", "Major Cyber Attack", "Submarine Strike"]
        evt = random.choice(events)

        targets_list = ["Oil Refinery", "LNG Processing Facility", "Offshore Oil Rig", "Coal Power Plant", "Nuclear Power Plant", "Advanced Fighter Jet Assembly", "Naval Submarine Base", "Upgraded Airbase", "Pine Gap Intelligence Base", "Zinc Refinery", "Nickel Refinery", "Tungsten Refinery"]
        valid_targets = [t for t in targets_list if self.facilities[t]["count"] > 0]
        targeted_fac_type = random.choice(valid_targets) if valid_targets else None
        targeted_fac = targeted_fac_type
        if targeted_fac_type == "Upgraded Airbase":
            built_airbases = self.airbase_names[:min(13, self.facilities["Upgraded Airbase"]["count"])]
            targeted_fac = random.choice(built_airbases) if built_airbases else None

        thaad_count = 0
        patriot_count = 0
        if targeted_fac and evt in ["Missile Barrage", "Airstrike", "Submarine Strike"]:
            thaad_count = self.facility_protections.get(targeted_fac, {}).get("THAAD System", 0)
            patriot_count = self.facility_protections.get(targeted_fac, {}).get("Patriot Battery", 0)

        has_anti_drone = self.facilities["Anti-Drone Package"]["count"] > 0
        has_naval_def = (self.facilities["Hobart Class Destroyer"]["count"] > 0 or self.facilities["Hunter Class Frigate"]["count"] > 0 or self.facilities["Mongami Frigate"]["count"] > 0) and self.facilities["Anti-Ship Hypersonic Missiles"]["count"] > 0
        has_cyber = self.facilities["Cyber Security Division"]["count"] > 0
        has_data_centers = self.facilities["Data Center"]["count"] > 0
        has_sat = self.facilities["Satellite Grid"]["count"] > 0
        has_subs_or_base = self.facilities["Naval Submarine Base"]["count"] > 0 or self.facilities["Nuclear Submarine (x3)"]["count"] > 0

        can_counter = False
        req_text = ""
        if evt in ["Missile Barrage", "Airstrike"]:
            can_counter = thaad_count > 0 or patriot_count > 0
            req_text = "Requires Assigned THAAD or Patriot"
        elif evt == "Drone Attack":
            can_counter = has_anti_drone
            req_text = "Requires Anti-Drone Package"
        elif evt == "Navy Attack":
            can_counter = has_naval_def
            req_text = "Requires Warship + Anti-Ship Hypersonic Missiles"
        elif evt == "Major Cyber Attack":
            can_counter = has_cyber and has_data_centers
            req_text = "Requires Cyber Division + Data Centers"
        elif evt == "Grid Sabotage":
            can_counter = self.police_spend.get() > 5.0
            req_text = "Requires > $5B Police Spend"
        elif evt == "Submarine Strike":
            pass

        def finish_war_event():
            if getattr(self, 'extra_war_event_pending', False):
                self.extra_war_event_pending = False
                self.trigger_war_event_director()

        def take_hit(from_failed_intercept=False):
            if targeted_fac and targeted_fac_type and self.facilities[targeted_fac_type]["count"] > 0:
                lost = targeted_fac
                self.facilities[targeted_fac_type]["count"] -= 1

                if self.facility_protections[lost]["THAAD System"] > 0:
                    self.facility_protections[lost]["THAAD System"] -= 1
                    self.facilities["THAAD System"]["count"] -= 1
                elif self.facility_protections[lost]["Patriot Battery"] > 0:
                    self.facility_protections[lost]["Patriot Battery"] -= 1
                    self.facilities["Patriot Battery"]["count"] -= 1

                if not hasattr(self, 'pending_war_damage'):
                    self.pending_war_damage = []
                self.pending_war_damage.append(targeted_fac_type)
                self.event_happy_mod -= 5.0
                messagebox.showerror("ATTACK IMPACT", f"The enemy {evt} hit! We lost 1x {lost}.")
                self.update_facilities_table()
            else:
                self.event_happy_mod -= 5.0
                messagebox.showerror("ATTACK IMPACT", f"The enemy {evt} hit! Infrastructure heavily damaged, public morale dropped.")

            if not from_failed_intercept:
                finish_war_event()

        def counter_attack():
            if evt in ["Missile Barrage", "Airstrike"]:
                thaad_c = 0
                if thaad_count > 0:
                    thaad_c = 40 + (thaad_count - 1) * 5
                    thaad_c = min(thaad_c, 75)
                    if has_sat: thaad_c += 8

                pat_c = 0
                if patriot_count > 0:
                    pat_c = 25 + (patriot_count - 1) * 6
                    pat_c = min(pat_c, 85)
                    if has_sat: pat_c += 5

                success = (random.random() * 100 < thaad_c) or (random.random() * 100 < pat_c)

                if not success:
                    messagebox.showerror("INTERCEPT FAILED", f"Your air defenses failed to intercept the {evt}!")
                    take_hit(from_failed_intercept=True)
                    return

            elif evt == "Drone Attack":
                self.anti_drone_uses += 1
                if self.anti_drone_uses >= 3:
                    self.facilities["Anti-Drone Package"]["count"] -= 1
                    self.anti_drone_uses = 0
                    messagebox.showwarning("Defenses Depleted", "An Anti-Drone Package was fully consumed!")
                    self.update_facilities_table()

            elif evt == "Navy Attack":
                self.hypersonic_uses += 1
                if self.hypersonic_uses >= 3:
                    self.facilities["Anti-Ship Hypersonic Missiles"]["count"] -= 1
                    self.hypersonic_uses = 0
                    messagebox.showwarning("Munitions Depleted", "Anti-Ship Hypersonic Missiles were completely used up!")
                    self.update_facilities_table()

            self.event_happy_mod += 2.0
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
            messagebox.showinfo("SUCCESSFUL INTERCEPT", f"Your defense systems successfully countered the enemy {evt}!")
            finish_war_event()

        if evt == "Submarine Strike":
            opts = []
            def do_intercept(method):
                chance = 0
                if method == "subs": chance = 60
                if method == "air": chance = 40
                if method == "both": chance = 85

                if random.random() * 100 < chance:
                    self.event_happy_mod += 2.0
                    self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
                    messagebox.showinfo("SUCCESSFUL INTERCEPT", f"Your {method} defenses successfully countered the enemy Submarine Strike!")
                    finish_war_event()
                else:
                    messagebox.showerror("INTERCEPT FAILED", "Your defenses failed to intercept the Submarine Strike!")
                    take_hit(from_failed_intercept=True)

            if has_subs_or_base:
                opts.append(("Submarine Interception", lambda: do_intercept("subs"), "#00843D"))
            if thaad_count > 0 or patriot_count > 0:
                opts.append(("Air Defences", lambda: do_intercept("air"), "#00843D"))
            if has_subs_or_base and (thaad_count > 0 or patriot_count > 0):
                opts.append(("Use Both (High Success)", lambda: do_intercept("both"), "#002B49"))

            if not opts:
                opts.append(("CANNOT COUNTER (Need Subs/Air Def)", take_hit, "#555555"))

            opts.append(("Brace for Impact", take_hit, "#D9381E"))

            desc = f"An enemy submarine has launched a cruise missile specifically targeting our {targeted_fac}!" if targeted_fac else "An enemy submarine has launched a cruise missile!"
            self.show_overlay("ENEMY SUBMARINE STRIKE DETECTED!", desc, "#8B0000", opts)
            return

        opts = []
        if can_counter:
            opts.append((f"Intercept / Counter ({req_text})", counter_attack, "#00843D"))
        else:
            opts.append((f"CANNOT COUNTER ({req_text})", take_hit, "#555555"))

        opts.append(("Brace for Impact (Take Damage)", take_hit, "#D9381E"))

        desc_text = f"The enemy has launched a {evt} specifically targeting our {targeted_fac}! Can we stop it?" if targeted_fac else f"The enemy has launched a {evt} against our homeland! Can we stop it?"
        self.show_overlay(f"ENEMY {evt.upper()} DETECTED!", desc_text, "#8B0000", opts)

    def trigger_war_ally_call(self):
        self.ally_called_this_war = True

        if self.war_opponent in ["Japan", "Philippines", "Taiwan"]:
            msg = f"{self.war_opponent} has called in regional allies to team against you!"
            self.war_tier = 3
        elif self.war_opponent in ["Russia", "China"]:
            msg = f"{self.war_opponent} has called in their superpower allies to team against you!"
            self.war_tier = 3
        elif self.war_opponent == "New Zealand":
            msg = "New Zealand has invoked their defense treaties and called the United States into the war!"
            self.war_tier = 3
        elif self.war_opponent == "Solomon Islands":
            msg = "The Solomon Islands has received massive military support from China! Their attack capabilities have increased and the war will end sooner."
            self.war_duration -= 5
            self.war_tier = 3
        else:
            msg = f"{self.war_opponent} has called for international allies, drastically escalating the conflict!"
            self.war_tier = 3

        def ack():
            self.update_war_ui()
            if getattr(self, 'extra_war_event_pending', False):
                self.extra_war_event_pending = False
                self.trigger_war_event_director()

        self.show_overlay(
            "⚠️ ALLY CALL EVENT",
            msg,
            "#8B0000",
            [("Acknowledge", ack, "#CCCCCC")]
        )

    def trigger_war_fuel_shortage(self):
        def fund():
            self.debt += 5.0
            self.event_inflation_mod += 2.0
            if getattr(self, 'extra_war_event_pending', False):
                self.extra_war_event_pending = False
                self.trigger_war_event_director()

        def ignore():
            self.event_happy_mod -= 10.0
            self.event_health_mod -= 5.0
            if getattr(self, 'extra_war_event_pending', False):
                self.extra_war_event_pending = False
                self.trigger_war_event_director()

        self.show_overlay(
            "⚠️ WAR FUEL SHORTAGE",
            "Due to a lack of domestic refineries and LNG plants, our wartime supply chains are suffering a massive fuel shortage!",
            "#D9381E",
            [
                ("Fund Emergency Relief ($5.0B, Infl +2%)", fund, "#00843D"),
                ("Ignore (Happy -10%, Health -5)", ignore, "#CCCCCC")
            ]
        )

    def trigger_war_event_director(self):
        choices = ["Attack"] * 10
        if self.foreign_relations < 50.0 and not getattr(self, "ally_called_this_war", False):
            choices.append("Ally Call")
        if self.facilities["Oil Refinery"]["count"] <= 3 and self.facilities["LNG Processing Facility"]["count"] <= 5:
            choices.extend(["Fuel Shortage"] * 2)

        choice = random.choice(choices)
        if choice == "Ally Call":
            self.trigger_war_ally_call()
        elif choice == "Fuel Shortage":
            self.trigger_war_fuel_shortage()
        else:
            self.trigger_enemy_war_event()

    def setup_laws_tab(self):
        canvas = tk.Canvas(self.tab_laws, bg="#F4F6F9")
        scrollbar = ttk.Scrollbar(self.tab_laws, orient="vertical", command=canvas.yview)
        self.laws_frame = tk.Frame(canvas, bg="#F4F6F9")

        self.laws_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.laws_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def laws_mousewheel(event):
            if getattr(event, "delta", 0):
                step = -1 if event.delta > 0 else 1
                canvas.yview_scroll(step, "units")
            elif getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", laws_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", laws_mousewheel)
        canvas.bind("<Button-5>", laws_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.render_laws()

    def render_laws(self):
        # Native Streamlit rendering is handled by render_laws_tab().
        return None
    def fund_employment(self):
        if self.unemployment <= 1.8:
            messagebox.showwarning("Limit Reached", "Unemployment is already at the minimum structural level (1.8%).")
            return

        self.debt += 10.0
        self.event_unemployment_mod -= 1.0
        self.event_inflation_mod += 0.5

        # Update the UI directly to reflect the change before the next tick
        self.recalculate_economy()
        self.lbl_unemp.config(text=f"{self.unemployment:.1f}%")
        self.lbl_debt.config(text=f"${self.debt:.1f}B AUD", fg="#FF6666" if self.debt > 0 else "#00FF66")

        messagebox.showinfo("Program Funded", "You have spent $10.0B AUD on Employment Programs.\nUnemployment has decreased by 1%, but Inflation increased by 0.5%.")

    def toggle_law(self, law_name):
        if not self.laws[law_name]["passed"]:
            if law_name == "Legalise Free Speech" and not self.laws["Abolish 18c"]["passed"]:
                messagebox.showerror("Law Blocked", "You must successfully pass the 'Abolish 18c' law before you can pass this bill!"); return
            if law_name == "Free TAFE" and not self.laws["Defund Private Universities"]["passed"]:
                messagebox.showerror("Law Blocked", "You must pass 'Defund Private Universities' before you can unlock this bill!"); return
            if law_name == "Anti-Corruption & Lobbying Act" and self.year == 2026:
                messagebox.showerror("Law Blocked", "This law can only be passed after your 1st term!"); return
            if law_name == "Dedicate 8% RAM to Gaming" and self.facilities["RAM Production Plant"]["count"] == 0:
                messagebox.showerror("Missing Infrastructure", "You must build a RAM Production Plant before you can pass this law!"); return
            if law_name == "Pass Hydrogen Bus Bill" and self.facilities["Hydrogen Fuel Facility"]["count"] == 0:
                messagebox.showerror("Missing Infrastructure", "You must build a Hydrogen Fuel Facility before you can pass this bill!"); return
            if self.senate_popularity < 50.0:
                aligned_parties = self.laws[law_name].get("align", []); demands=[]
                if "Greens" in aligned_parties: demands.append({"party":"The Greens","setting_key":"climate_spend","text":"Increase Climate Change Funding by $2.0B AUD/mo","action":lambda:self.climate_spend.set(min(13.0,self.climate_spend.get()+2.0)),"get_val":lambda:self.climate_spend.get()})
                if "Liberal" in aligned_parties: demands.append({"party":"Liberal Party","setting_key":"company_tax_rate","text":"Cut Company Tax Rate by 2.0%","action":lambda:self.company_tax_rate.set(max(0.0,self.company_tax_rate.get()-2.0)),"get_val":lambda:self.company_tax_rate.get()})
                if "Nationals" in aligned_parties: demands.append({"party":"The Nationals","setting_key":"infra_spend","text":"Increase Public Infrastructure Funding by $1.5B AUD/mo","action":lambda:self.infra_spend.set(min(18.0,self.infra_spend.get()+1.5)),"get_val":lambda:self.infra_spend.get()})
                if "One Nation" in aligned_parties: demands.append({"party":"One Nation","setting_key":"immigration_policy","text":"Lower Overseas Immigration to Low (15k/mo)","action":lambda:self.immigration_policy.set("Low (15k/mo)"),"get_val":lambda:self.immigration_policy.get()})
                if not demands:
                    messagebox.showinfo("Bill Blocked", f"Your Senate Popularity is {self.senate_popularity:.1f}% (under 50%). No political parties support this bill's ideological stance, so it cannot be passed!"); return
                demand=random.choice(demands)
                st.session_state["pending_law_demand"]={"law_name":law_name,"demand":demand}
                st.session_state["confirmation"]={"title":"Senate Demand - Bill Blocked","message":f"Your Senate Popularity is {self.senate_popularity:.1f}% (under 50%). The Senate blocked '{law_name}'!\n\n{demand['party']} aligns with this bill and offers to vote WITH you, but DEMANDS that you:\n👉 {demand['text']}\n\n(Accepting this locks the modified setting for 3 months!)\nDo you accept their demand to get their backing and pass your law?","action":"accept_law_demand"}
                return
            self.laws[law_name]["passed"] = True; self.senate_popularity=min(100.0,self.senate_popularity+2.0)
            if not hasattr(self,'recent_news'): self.recent_news=[]
            if law_name == "Block Foreign Property Purchases": self.recent_news.append("Real estate market shakes as foreigners are officially banned from buying Australian homes.")
            elif law_name == "ADF Domestic Dispatch Act": self.recent_news.append("Military on the streets! ADF deployed domestically to combat rising crime waves.")
            elif law_name == "Illigalise Santanism": self.recent_news.append("Controversial new law outlaws Satanism nationwide, sparking severe underground protests.")
            elif law_name == "Universal Basic Income Trial": self.recent_news.append("Citizens celebrate as Universal Basic Income trial injects massive cash into local economies.")
            elif law_name == "Ban E-Cigarettes & Vapes": self.recent_news.append("Vape ban fully enforced! Health improves, but black market crime spikes significantly.")
            else: self.recent_news.append(f"New Legislation Passed: '{law_name}' becomes official federal law.")
            if law_name == "Illigalise Santanism":
                self.satanism_passed_count += 1
                if self.satanism_passed_count == 1: self.force_market_crash=True
                elif self.satanism_passed_count >= 2: self.satanism_assassination_timer=random.randint(2,6)
            if law_name == "Block Foreign Property Purchases":
                months=24 if self.immigration_policy.get()=="Closed Borders (0/mo)" else 12; self.housing_crisis_blocked_until=self.term_month+months
        else:
            self.laws[law_name]["passed"]=False; self.senate_popularity=max(0.0,self.senate_popularity-2.0)
            if law_name == "Block Foreign Property Purchases": self.housing_crisis_blocked_until=0
        self.recalculate_economy()
    def setup_immigration_tab(self):
        lbl = tk.Label(self.tab_immigration, text="Set Monthly Net Overseas Migration Quota:", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        lbl.pack(anchor="w", padx=15, pady=10)
        options = ["Closed Borders (0/mo)", "Low (15k/mo)", "Moderate (35k/mo)", "High (75k/mo)", "Massive Open (150k/mo)"]
        for opt in options:
            tk.Radiobutton(self.tab_immigration, text=opt, variable=self.immigration_policy, value=opt,
                           bg="#F4F6F9", fg="black", selectcolor="#E0E0E0", font=("Helvetica", 11), command=self.recalculate_economy).pack(anchor="w", padx=30, pady=5)

    def setup_trade_tab(self):
        action_f = tk.LabelFrame(self.tab_trade, text=" Emergency Trade Actions ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        action_f.pack(fill="x", padx=15, pady=10)

        self.btn_broad_tariffs = tk.Button(action_f, text="Enact Broad Tariffs (3 Months)", bg="#D9381E", fg="black", font=("Helvetica", 10, "bold"), command=self.enact_tariffs)
        self.btn_broad_tariffs.pack(side="left", padx=15, pady=10)

        self.btn_toggle_sanctions = tk.Button(action_f, text="Toggle Hard Sanctions", bg="#D9381E", fg="black", font=("Helvetica", 10, "bold"), command=self.toggle_sanctions)
        self.btn_toggle_sanctions.pack(side="left", padx=15, pady=10)

        top_f = tk.LabelFrame(self.tab_trade, text=" Resource Export Levies (%) ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        top_f.pack(fill="x", padx=15, pady=10)
        for res, var in self.resource_levies.items():
            self.create_slider(top_f, f"Export Levy - {res}:", var, 0.0, 30.0, is_percent=True)

        tariff_f = tk.LabelFrame(self.tab_trade, text=" Import Tariffs (%) ", bg="#F4F6F9", fg="black", font=("Helvetica", 11, "bold"))
        tariff_f.pack(fill="x", padx=15, pady=10)
        for country, var in self.tariffs.items():
            self.create_slider(tariff_f, f"Tariff - {country}:", var, 0.0, 30.0, is_percent=True)

    def enact_tariffs(self):
        if self.tariffs_timer > 0:
            return
        self.tariffs_timer = 3
        self.tariffs_boost_active = False
        messagebox.showinfo("Tariffs Enacted", "Broad Tariffs Enacted!\nInflation will rise by 5% and happiness will drop by 3% for the next 3 months.")
        self.recalculate_economy()

    def toggle_sanctions(self):
        self.sanctions_active = not self.sanctions_active
        state = "ON" if self.sanctions_active else "OFF"
        messagebox.showinfo("Sanctions Updated", f"Hard Sanctions are now {state}.\nWhile active, Inflation is increased by 15% and happiness drops by 3%.")
        self.recalculate_economy()

    def trigger_net_zero_push(self):
        self.net_zero_push_occurred = True
        def accept():
            self.net_zero_accepted = True
            self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
            self.event_inflation_mod += 3.0
        def reject():
            self.net_zero_accepted = False
            self.event_happy_mod += 15.0
        self.show_overlay(
            "🌍 GLOBAL NET ZERO PUSH",
            "The UN is demanding strict emission cuts. Will you commit to aggressive Net Zero targets?",
            "#00843D",
            [
                ("Commit to Net Zero (-$2B/mo Revenue, +3% Inflation, +$15 Power Bills)", accept, "#00843D"),
                ("Reject Targets (-10% Foreign Rel, +15% Happy)", reject, "#D9381E")
            ]
        )

    def trigger_black_market(self):
        def ignore():
            self.event_crime_mod += 10.0
            self.event_happy_mod -= 5.0
        def police():
            self.debt += 1.5
            self.event_inflation_mod += 1.0
            self.black_market_police_timer = 3
        def asio():
            self.debt += 15.0
            self.event_happy_mod += 5.0
            self.event_inflation_mod += 0.25
        self.show_overlay(
            "⚠️ BLACK MARKET BOOM",
            "High sin taxes have created a booming underground black market. Crime is escalating rapidly.",
            "#000000",
            [
                ("Ignore (-5% Happy, +10 Crime)", ignore, "#CCCCCC"),
                ("Police Package ($1.5B AUD, +1% Infl, Solves in 3mo)", police, "#002B49"),
                ("Deploy ASIO ($15.0B AUD, +5% Happy, +0.25% Infl, Instant Fix)", asio, "#00843D")
            ]
        )

    def trigger_shale_oil(self):
        def ignore():
            self.event_happy_mod -= 15.0
            self.shale_oil_penalty = 0.50
        def drill():
            self.debt += 20.0
            self.shale_boom_timer = 250
            self.shale_oil_penalty = -0.60
        self.show_overlay(
            "🛢️ SHALE OIL BOOM",
            "Massive shale oil reserves discovered! Environmentalists protest, but the economic potential is huge.",
            "#8B0000",
            [
                ("Ignore Discovery (You suck)", ignore, "#CCCCCC"),
                ("Drill Baby Drill ($20B AUD, Increases Fuel Production)", drill, "#00843D")
            ]
        )

    # --- MARKET TAB SETUP ---
    def setup_market_tab(self):
        header_lbl = tk.Label(self.tab_market, text="📈 Live Commodity Market & Average Prices (AUD)", bg="#F4F6F9", fg="black", font=("Helvetica", 13, "bold"))
        header_lbl.pack(anchor="w", padx=15, pady=10)

        desc_lbl = tk.Label(self.tab_market, text="Monitor market values affected logically by levies, tariffs, refining/processing infrastructure, and disasters.\nThese prices directly influence inflation, energy bills, and overall public happiness.", bg="#F4F6F9", fg="black", font=("Helvetica", 10))
        desc_lbl.pack(anchor="w", padx=15, pady=2)

        self.market_tree = ttk.Treeview(self.tab_market, columns=("Commodity", "Unit", "Current Price", "Base Price", "Base Demand", "Demand"), show="headings")
        self.market_tree.heading("Commodity", text="Resource / Commodity")
        self.market_tree.heading("Unit", text="Unit Measurement")
        self.market_tree.heading("Current Price", text="Current Price (AUD)")
        self.market_tree.heading("Base Price", text="Base Price (AUD)")
        self.market_tree.heading("Base Demand", text="Base Demand (%)")
        self.market_tree.heading("Demand", text="Demand (%)")

        self.market_tree.column("Commodity", width=160)
        self.market_tree.column("Unit", width=140)
        self.market_tree.column("Current Price", width=150)
        self.market_tree.column("Base Price", width=150)
        self.market_tree.column("Base Demand", width=130)
        self.market_tree.column("Demand", width=110)

        self.market_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.update_market_table()

    def update_market_table(self):
        if not hasattr(self, 'market_tree'):
            return
        try:
            if not self.market_tree.winfo_exists():
                return
            for item in self.market_tree.get_children():
                self.market_tree.delete(item)

            for comm, data in self.market_prices.items():
                price_str = f"${data['current']:.3f}" if data['current'] < 1.0 else f"${data['current']:.2f}"
                base_str = f"${data['base']:.3f}" if data['base'] < 1.0 else f"${data['base']:.2f}"
                base_demand_str = f"{data.get('base_demand', 100.0):.0f}%"
                demand_str = f"{data.get('demand', 100.0):.1f}%"
                self.market_tree.insert("", "end", values=(
                    comm, data["unit"], price_str, base_str, base_demand_str, demand_str
                ))
        except tk.TclError:
            return

    def update_market_calculations(self):
        # Calculate dynamic AUD commodity market prices
        oil_ref = self.facilities["Oil Refinery"]["count"]
        oil_rigs = self.facilities["Offshore Oil Rig"]["count"]
        iron_smelt = self.facilities["Iron Ore Smelter"]["count"]
        gold_ref = self.facilities["Gold Refinery"]["count"]
        lng_proc = self.facilities["LNG Processing Facility"]["count"]
        lith_proc = self.facilities["Lithium Processing Plant"]["count"]
        uran_mine = self.facilities["Uranium Mine"]["count"]
        rare_ref = self.facilities["Rare Earths Refinery"]["count"]
        cop_smelt = self.facilities["Copper Smelting Plant"]["count"]
        ram_plant = self.facilities["RAM Production Plant"]["count"]
        desal_plant = self.facilities["Desalination Plant"]["count"]
        flood_plant = self.facilities["Flood-Catchment Plant"]["count"]
        zircon_ref = self.facilities["Zirconium Refinery"]["count"]
        zinc_ref = self.facilities["Zinc Refinery"]["count"]
        nickel_ref = self.facilities["Nickel Refinery"]["count"]
        tungsten_ref = self.facilities["Tungsten Refinery"]["count"]

        oil_levy = self.resource_levies["Crude Oil"].get()
        iron_levy = self.resource_levies["Iron (Raw Material)"].get()
        gold_levy = self.resource_levies["Gold"].get()
        lith_levy = self.resource_levies["Lithium"].get()
        uran_levy = self.resource_levies["Uranium"].get()
        cop_levy = self.resource_levies["Copper"].get()
        ram_levy = self.resource_levies["RAM (Req. Plant)"].get()
        zircon_levy = self.resource_levies["Zirconium"].get()
        zinc_levy = self.resource_levies["Zinc"].get()
        nickel_levy = self.resource_levies["Nickel"].get()
        tungsten_levy = self.resource_levies["Tungsten"].get()

        avg_tariff = sum(v.get() for v in self.tariffs.values()) / len(self.tariffs)
        natural_resource_tariff = self.tariffs["Energy & Natural Resources"].get()
        agricultural_tariff = self.tariffs["Agricultural products"].get()
        infl_mult = max(0.5, 1.0 + (self.inflation - 2.8) * 0.05)

        # Water ($ / Litre)
        water_base = 0.003
        water_price = water_base * infl_mult
        water_factors = []
        if desal_plant > 0:
            water_price *= (1.0 - min(0.6, desal_plant * 0.08))
            water_factors.append(f"Desalination x{desal_plant}")
        if flood_plant > 0:
            water_price *= (1.0 - min(0.3, flood_plant * 0.05))
            water_factors.append(f"Catchment x{flood_plant}")
        if not water_factors: water_factors.append("Standard Supply")
        self.market_prices["Water"]["current"] = max(0.0005, water_price)
        self.market_prices["Water"]["factors"] = ", ".join(water_factors)

        # Crude Oil ($ / Litre)
        crude_price = 1.10 * infl_mult
        if natural_resource_tariff > 0:
            crude_price *= (1.0 + min(0.20, natural_resource_tariff * 0.005))
        crude_factors = ["Global Base"]
        if natural_resource_tariff > 0:
            crude_factors.append(f"Natural Resource Tariff +{natural_resource_tariff:.1f}%")
        if getattr(self, 'shale_oil_penalty', 0.0) != 0.0:
            crude_price += self.shale_oil_penalty
            crude_factors.append(f"Shale Event ({self.shale_oil_penalty:+.2f})")
        self.market_prices["Crude Oil"]["current"] = max(0.1, crude_price)
        self.market_prices["Crude Oil"]["factors"] = ", ".join(crude_factors)

        # Beef ($ / Kg)
        beef_base = 12.00
        beef_price = beef_base * infl_mult
        if agricultural_tariff > 0:
            beef_price *= (1.0 + min(0.20, agricultural_tariff * 0.005))
        beef_factors = []
        if agricultural_tariff > 0:
            beef_factors.append(f"Agricultural Tariff +{agricultural_tariff:.1f}%")
        beef_levy = self.resource_levies["Beef"].get()
        if beef_levy > 0:
            beef_price *= (1.0 - beef_levy * 0.015)
            beef_factors.append(f"Beef Levy {beef_levy:.1f}%")
        if not beef_factors: beef_factors.append("Agricultural Standard")
        self.market_prices["Beef"]["current"] = max(4.0, beef_price)
        self.market_prices["Beef"]["factors"] = ", ".join(beef_factors)

        # Steel ($ / Kg)
        steel_price = 1.20 * infl_mult * (1.0 + avg_tariff * 0.01)
        if natural_resource_tariff > 0:
            steel_price *= (1.0 + min(0.20, natural_resource_tariff * 0.005))
        steel_factors = []
        if natural_resource_tariff > 0:
            steel_factors.append(f"Natural Resource Tariff +{natural_resource_tariff:.1f}%")
        if iron_smelt > 0:
            steel_price *= (1.0 - min(0.5, iron_smelt * 0.08))
            steel_factors.append(f"Iron Smelters x{iron_smelt}")
        if iron_levy > 0:
            steel_price *= (1.0 - iron_levy * 0.005)
            steel_factors.append(f"Iron Levy {iron_levy:.1f}%")
        steel_levy = self.resource_levies["Steel"].get()
        if steel_levy > 0:
            steel_price *= (1.0 - steel_levy * 0.01)
            steel_factors.append(f"Steel Levy {steel_levy:.1f}%")
        if not steel_factors: steel_factors.append("Global Market Baseline")
        self.market_prices["Steel"]["current"] = max(0.2, steel_price)
        self.market_prices["Steel"]["factors"] = ", ".join(steel_factors)

        # Gold ($ / Gram)
        gold_price = 110.00 * infl_mult
        gold_factors = []
        if gold_ref > 0:
            gold_price *= (1.0 - min(0.4, gold_ref * 0.10))
            gold_factors.append(f"Gold Refineries x{gold_ref}")
        if gold_levy > 0:
            gold_price *= (1.0 - gold_levy * 0.005)
            gold_factors.append(f"Export Levy {gold_levy:.1f}%")
        if not gold_factors: gold_factors.append("Global Reserve Standard")
        self.market_prices["Gold"]["current"] = max(20.0, gold_price)
        self.market_prices["Gold"]["factors"] = ", ".join(gold_factors)

        # Uranium ($ / Kg)
        uran_price = 180.00 * infl_mult
        uran_factors = []
        if uran_mine > 0:
            uran_price *= (1.0 - min(0.6, uran_mine * 0.12))
            uran_factors.append(f"Uranium Mines x{uran_mine}")
        if uran_levy > 0:
            uran_price *= (1.0 - uran_levy * 0.008)
            uran_factors.append(f"Levy {uran_levy:.1f}%")
        if not uran_factors: uran_factors.append("Global Nuclear Market")
        self.market_prices["Uranium"]["current"] = max(30.0, uran_price)
        self.market_prices["Uranium"]["factors"] = ", ".join(uran_factors)

        # Lithium ($ / Kg)
        lith_price = 25.00 * infl_mult
        lith_factors = []
        if lith_proc > 0:
            lith_price *= (1.0 - min(0.5, lith_proc * 0.10))
            lith_factors.append(f"Processing Plants x{lith_proc}")
        if lith_levy > 0:
            lith_price *= (1.0 - lith_levy * 0.007)
            lith_factors.append(f"Export Levy {lith_levy:.1f}%")
        if not lith_factors: lith_factors.append("Battery Industry Standard")
        self.market_prices["Lithium"]["current"] = max(5.0, lith_price)
        self.market_prices["Lithium"]["factors"] = ", ".join(lith_factors)

        # Zinc ($ / Kg)
        zinc_price = 4.00 * infl_mult
        zinc_factors = []
        if zinc_ref > 0:
            zinc_price *= (1.0 - min(0.5, zinc_ref * 0.10))
            zinc_factors.append(f"Zinc Refineries x{zinc_ref}")
        if zinc_levy > 0:
            zinc_price *= (1.0 - zinc_levy * 0.006)
            zinc_factors.append(f"Export Levy {zinc_levy:.1f}%")
        if not zinc_factors: zinc_factors.append("Global Metal Standard")
        self.market_prices["Zinc"]["current"] = max(1.0, zinc_price)
        self.market_prices["Zinc"]["factors"] = ", ".join(zinc_factors)

        # Nickel ($ / Kg)
        nickel_price = 20.00 * infl_mult
        nickel_factors = []
        if nickel_ref > 0:
            nickel_price *= (1.0 - min(0.5, nickel_ref * 0.10))
            nickel_factors.append(f"Nickel Refineries x{nickel_ref}")
        if nickel_levy > 0:
            nickel_price *= (1.0 - nickel_levy * 0.006)
            nickel_factors.append(f"Export Levy {nickel_levy:.1f}%")
        if not nickel_factors: nickel_factors.append("Global Metal Standard")
        self.market_prices["Nickel"]["current"] = max(5.0, nickel_price)
        self.market_prices["Nickel"]["factors"] = ", ".join(nickel_factors)

        # Tungsten ($ / Kg)
        tungsten_price = 40.00 * infl_mult
        tungsten_factors = []
        if tungsten_ref > 0:
            tungsten_price *= (1.0 - min(0.5, tungsten_ref * 0.10))
            tungsten_factors.append(f"Tungsten Refineries x{tungsten_ref}")
        if tungsten_levy > 0:
            tungsten_price *= (1.0 - tungsten_levy * 0.006)
            tungsten_factors.append(f"Export Levy {tungsten_levy:.1f}%")
        if not tungsten_factors: tungsten_factors.append("Global Metal Standard")
        self.market_prices["Tungsten"]["current"] = max(10.0, tungsten_price)
        self.market_prices["Tungsten"]["factors"] = ", ".join(tungsten_factors)

        # Coal ($ / Kg)
        coal_price = 0.20 * infl_mult
        if "United States" in self.defeated_countries:
            coal_price *= 0.5
        coal_factors = ["Domestic Mining Base"]
        self.market_prices["Coal"]["current"] = max(0.05, coal_price)
        self.market_prices["Coal"]["factors"] = ", ".join(coal_factors)

        # LNG ($ / Kg)
        lng_price = 0.70 * infl_mult
        lng_factors = []
        if lng_proc > 0:
            lng_price *= (1.0 - min(0.5, lng_proc * 0.12))
            lng_factors.append(f"LNG Facilities x{lng_proc}")
        if self.fuel_crisis_occurred and not (oil_ref >= 10 or lng_proc >= 10):
            lng_price += 0.80
            lng_factors.append("Fuel Crisis Impact (+0.80)")
        if not lng_factors: lng_factors.append("Export Grid Standard")
        self.market_prices["LNG"]["current"] = max(0.1, lng_price)
        self.market_prices["LNG"]["factors"] = ", ".join(lng_factors)

        # Petrol ($ / Litre)
        petrol_price = (2.00 + (self.fuel_excise_rate.get() - 44.0) * 0.01) * infl_mult
        if natural_resource_tariff > 0:
            petrol_price *= (1.0 + min(0.20, natural_resource_tariff * 0.005))
        petrol_factors = []
        if natural_resource_tariff > 0:
            petrol_factors.append(f"Natural Resource Tariff +{natural_resource_tariff:.1f}%")
        if oil_ref > 0 or oil_rigs > 0:
            petrol_price *= (1.0 - min(0.45, (oil_ref * 0.06) + (oil_rigs * 0.04)))
            petrol_factors.append(f"Refineries/Rigs x{oil_ref + oil_rigs}")

        if getattr(self, 'shale_oil_penalty', 0.0) != 0.0:
            petrol_price += self.shale_oil_penalty
            petrol_factors.append(f"Shale Event ({self.shale_oil_penalty:+.2f})")

        crude_oil_levy = self.resource_levies["Crude Oil"].get()
        petrol_levy = self.resource_levies["Petrol"].get()
        diesel_levy = self.resource_levies["Diesel"].get()

        if crude_oil_levy > 0:
            petrol_price *= (1.0 - crude_oil_levy * 0.01)
            petrol_factors.append(f"Crude Oil Levy {crude_oil_levy:.1f}%")
        if petrol_levy > 0:
            petrol_price *= (1.0 - petrol_levy * 0.02)
            petrol_factors.append(f"Petrol Levy {petrol_levy:.1f}%")
        if self.fuel_crisis_occurred and not (oil_ref >= 10 or lng_proc >= 10):
            petrol_price += 1.20
            petrol_factors.append("Fuel Crisis Impact (+$1.20)")
        if self.laws.get("Pass Hydrogen Bus Bill", {}).get("passed"):
            petrol_price -= 0.10
            petrol_factors.append("Hydrogen Bus Bill (-$0.10)")
        if not petrol_factors: petrol_factors.append("Import Dependent Standard")

        petrol_floor = 1.20 if (oil_ref < 6 or self.facilities["Oil Extraction Field"]["count"] < 2) else 0.5
        self.market_prices["Petrol"]["current"] = max(petrol_floor, petrol_price)
        self.market_prices["Petrol"]["factors"] = ", ".join(petrol_factors)

        # Diesel ($ / Litre)
        diesel_price = (2.15 + (self.fuel_excise_rate.get() - 44.0) * 0.01) * infl_mult
        if natural_resource_tariff > 0:
            diesel_price *= (1.0 + min(0.20, natural_resource_tariff * 0.005))
        diesel_factors = []
        if natural_resource_tariff > 0:
            diesel_factors.append(f"Natural Resource Tariff +{natural_resource_tariff:.1f}%")
        if oil_ref > 0 or oil_rigs > 0:
            diesel_price *= (1.0 - min(0.45, (oil_ref * 0.06) + (oil_rigs * 0.04)))
            diesel_factors.append(f"Refineries/Rigs x{oil_ref + oil_rigs}")

        if getattr(self, 'shale_oil_penalty', 0.0) != 0.0:
            diesel_price += self.shale_oil_penalty
            diesel_factors.append(f"Shale Event ({self.shale_oil_penalty:+.2f})")

        if crude_oil_levy > 0:
            diesel_price *= (1.0 - crude_oil_levy * 0.01)
            diesel_factors.append(f"Crude Oil Levy {crude_oil_levy:.1f}%")
        if diesel_levy > 0:
            diesel_price *= (1.0 - diesel_levy * 0.02)
            diesel_factors.append(f"Diesel Levy {diesel_levy:.1f}%")
        if self.fuel_crisis_occurred and not (oil_ref >= 10 or lng_proc >= 10):
            diesel_price += 1.25
            diesel_factors.append("Fuel Crisis Impact (+$1.25)")
        if self.laws.get("Pass Hydrogen Bus Bill", {}).get("passed"):
            diesel_price -= 0.10
            diesel_factors.append("Hydrogen Bus Bill (-$0.10)")
        if not diesel_factors: diesel_factors.append("Freight Import Standard")

        diesel_floor = 1.20 if (oil_ref < 6 or self.facilities["Oil Extraction Field"]["count"] < 2) else 0.5
        self.market_prices["Diesel"]["current"] = max(diesel_floor, diesel_price)
        self.market_prices["Diesel"]["factors"] = ", ".join(diesel_factors)

        # Copper ($ / Kg)
        cop_price = 14.00 * infl_mult
        if natural_resource_tariff > 0:
            cop_price *= (1.0 + min(0.20, natural_resource_tariff * 0.005))
        cop_factors = []
        if natural_resource_tariff > 0:
            cop_factors.append(f"Natural Resource Tariff +{natural_resource_tariff:.1f}%")
        if cop_smelt > 0:
            cop_price *= (1.0 - min(0.5, cop_smelt * 0.10))
            cop_factors.append(f"Copper Smelters x{cop_smelt}")
        if cop_levy > 0:
            cop_price *= (1.0 - cop_levy * 0.006)
            cop_factors.append(f"Export Levy {cop_levy:.1f}%")
        if not cop_factors: cop_factors.append("Global Metal Standard")
        self.market_prices["Copper"]["current"] = max(3.0, cop_price)
        self.market_prices["Copper"]["factors"] = ", ".join(cop_factors)

        # RAM ($ / GB)
        ram_price = 12.00 * infl_mult
        ram_factors = []
        if ram_plant > 0:
            ram_price *= (1.0 - min(0.6, ram_plant * 0.25))
            ram_factors.append(f"RAM Plants x{ram_plant}")

        zinc_mkt = self.market_prices["Zinc"]["current"]
        nickel_mkt = self.market_prices["Nickel"]["current"]
        copper_mkt = self.market_prices["Copper"]["current"]

        if zinc_mkt > 4.0 or nickel_mkt > 20.0 or copper_mkt > 14.0:
            ram_price += (zinc_mkt - 4.0)*0.2 + (nickel_mkt - 20.0)*0.1 + (copper_mkt - 14.0)*0.1
            ram_factors.append("Critical Metals Cost (+)")
        elif zinc_mkt < 4.0 or nickel_mkt < 20.0 or copper_mkt < 14.0:
            ram_price -= max(0, (4.0 - zinc_mkt)*0.2 + (20.0 - nickel_mkt)*0.1 + (14.0 - copper_mkt)*0.1)
            ram_factors.append("Critical Metals Discount (-)")

        if self.laws["Dedicate 8% RAM to Gaming"]["passed"]:
            ram_price *= 1.15
            ram_factors.append("Gaming Mandate (+15% Demand)")
        if ram_levy > 0:
            ram_price *= (1.0 + ram_levy * 0.005)
            ram_factors.append(f"RAM Levy {ram_levy:.1f}%")
        if not ram_factors: ram_factors.append("Import Tech Chip Standard")
        self.market_prices["RAM"]["current"] = max(2.0, ram_price)
        self.market_prices["RAM"]["factors"] = ", ".join(ram_factors)

        # Demand responds to price. Lower prices increase demand, which nudges prices back upward modestly.
        for comm, data in self.market_prices.items():
            if comm == "Electricity":
                continue
            base_price = max(float(data["base"]), 0.000001)
            current_price = max(float(data["current"]), 0.000001)
            demand_ratio = (base_price / current_price) ** 0.5
            demand_ratio = max(0.5, min(1.5, demand_ratio))
            data["demand"] = min(100.0, data.get("base_demand", 100.0) * demand_ratio)
            price_gap = base_price - current_price
            feedback_strength = min(0.10, abs(demand_ratio - 1.0) * 0.20)
            data["current"] = max(0.000001, current_price + (price_gap * feedback_strength))

        power_mix = self.calculate_power_mix()
        self.apply_power_mix_demand_effects(power_mix)
        self.update_market_table()

    # --- ECONOMIC SIMULATION ENGINE ---
    def recalculate_economy(self):
        # Zirconium Refinery discount for Anti-Ship Hypersonic Missiles
        zircon_ref_count = self.facilities["Zirconium Refinery"]["count"]
        discount = min(0.25, zircon_ref_count * 0.05)
        self.facilities["Anti-Ship Hypersonic Missiles"]["cost"] = round(2.0 * (1.0 - discount), 2)

        # Enforce party demand locks
        for key, lock in list(self.locked_settings.items()):
            if key == "climate_spend" and self.climate_spend.get() != lock["val"]:
                self.climate_spend.set(lock["val"])
                messagebox.showwarning("Locked Setting", f"Climate Change Funding is locked at ${lock['val']}B AUD by agreement with {lock['party']} ({lock['months']} months remaining)!")
            elif key == "company_tax_rate" and self.company_tax_rate.get() != lock["val"]:
                self.company_tax_rate.set(lock["val"])
                messagebox.showwarning("Locked Setting", f"Company Tax Rate is locked at {lock['val']}% by agreement with {lock['party']} ({lock['months']} months remaining)!")
            elif key == "infra_spend" and self.infra_spend.get() != lock["val"]:
                self.infra_spend.set(lock["val"])
                messagebox.showwarning("Locked Setting", f"Infrastructure Funding is locked at ${lock['val']}B AUD by agreement with {lock['party']} ({lock['months']} months remaining)!")
            elif key == "immigration_policy" and self.immigration_policy.get() != lock["val"]:
                self.immigration_policy.set(lock["val"])
                messagebox.showwarning("Locked Setting", f"Immigration Policy is locked at {lock['val']} by agreement with {lock['party']} ({lock['months']} months remaining)!")

        immig_map = {
            "Closed Borders (0/mo)": (0, 5, -0.5, -1.0, -2.5),
            "Low (15k/mo)": (15000, 0, 0.2, 0.2, 0.5),
            "Moderate (35k/mo)": (35000, -3, 0.8, 1.0, 3.0),
            "High (75k/mo)": (75000, -8, 2.5, 3.0, 7.5),
            "Massive Open (150k/mo)": (150000, -15, 5.0, 6.0, 15.0)
        }

        monthly_immig, immig_crime_impact, infl_impact, rev_impact, happy_impact = immig_map[self.immigration_policy.get()]

        oil_gas_plants = self.facilities["Oil Refinery"]["count"] + self.facilities["LNG Processing Facility"]["count"] + self.facilities["Offshore Oil Rig"]["count"]
        open_cycle = self.facilities["Open-Cycle Gas Plant"]["count"]
        combined_cycle = self.facilities["Combined Cycle Gas Plant"]["count"]
        nuke_count = self.facilities["Nuclear Power Plant"]["count"]
        coal_count = self.facilities["Coal Power Plant"]["count"]
        solar_count = self.facilities["Solar Farm Grid"]["count"]
        flood_plants = self.facilities["Flood-Catchment Plant"]["count"]
        desal_plants = self.facilities["Desalination Plant"]["count"]
        data_centers = self.facilities["Data Center"]["count"]

        self.emissions = 45.0 + (coal_count * 15.0) + (oil_gas_plants * 5.0) - (solar_count * 3.5) - (nuke_count * 3.5)
        if self.climate_spend.get() <= 0.1 and self.net_zero_spend.get() <= 0.1:
            self.emissions += 10.0

        if self.emissions >= 100.0:
            self.emissions = 100.0
            self.carbon_sanctions_active = True
        else:
            self.carbon_sanctions_active = False

        self.foreign_relations = 100.0
        self.foreign_relations -= sum(v.get() for v in self.tariffs.values()) * 2.0
        if self.is_at_war:
            self.foreign_relations -= 40.0
        if self.sanctions_active:
            self.foreign_relations -= 30.0
        if getattr(self, 'net_zero_accepted', None) == False:
            self.foreign_relations -= 10.0

        if getattr(self, 'nuclear_sanctions', False):
            self.foreign_relations = 0.0

        self.foreign_relations = max(0.0, min(100.0, self.foreign_relations))

        try:
            if self.prog_foreign_rel.winfo_exists():
                self.prog_foreign_rel['value'] = self.foreign_relations
            if self.lbl_foreign_rel.winfo_exists():
                self.lbl_foreign_rel.config(text=f"{self.foreign_relations:.1f}%")
        except tk.TclError:
            pass

        effective_income_tax = (self.tax_bracket_15.get() * 0.15) + (self.tax_bracket_30.get() * 0.40) + \
                               (self.tax_bracket_37.get() * 0.30) + (self.tax_bracket_45.get() * 0.15)

        cgt_val_rate = self.cgt_rate.get()
        fbt_val_rate = self.fbt_rate.get()

        tax_rev = (effective_income_tax * 0.8) + (self.company_tax_rate.get() * 0.4) + \
                  (self.gst_rate.get() * 0.6) + (self.super_tax_rate.get() * 0.15) + \
                  (self.fuel_excise_rate.get() * 0.04) + (cgt_val_rate * 0.2) + \
                  (self.land_tax.get() * 0.3) + \
                  (self.sin_tax.get() * 0.08) + (fbt_val_rate * 0.15) + \
                  (self.small_business_tax.get() * 0.15) + (self.payroll_tax.get() * 0.2)

        # Capital Gains & Negative Gearing strict penalty rule
        ng_val = self.negative_gearing.get()
        tax_rev += (100.0 - ng_val) * 0.05
        happy_impact -= (100.0 - ng_val) * 0.75

        cgt_val = self.cgt_discount.get()
        if cgt_val < 50.0:
            happy_impact -= (50.0 - cgt_val) * 0.75

        happy_impact -= (cgt_val_rate - 25.0) * 0.15
        happy_impact -= (fbt_val_rate - 47.0) * 0.10
        happy_impact -= (self.payroll_tax.get() - 5.0) * 0.2

        # Sin Tax Overhaul
        sin_tax_val = self.sin_tax.get()
        sin_crime_impact = 0.0
        if sin_tax_val < 65.0:
            sin_happy_impact = (65.0 - sin_tax_val) * 1.0
            sin_crime_impact = (65.0 - sin_tax_val) * 0.5  # Increased crime when cheap
        else:
            sin_happy_impact = -(sin_tax_val - 65.0) * 1.5
            sin_crime_impact = -(sin_tax_val - 65.0) * 0.8  # Decreased crime when heavily taxed
        happy_impact += sin_happy_impact

        tax_happiness_penalty = ((self.tax_bracket_15.get() - 15.0) * 0.5) + \
                                ((self.tax_bracket_30.get() - 30.0) * 0.8) + \
                                ((self.tax_bracket_37.get() - 37.0) * 0.4) + \
                                ((self.tax_bracket_45.get() - 45.0) * 0.2) + \
                                ((self.company_tax_rate.get() - 30.0) * 0.5) + \
                                ((self.gst_rate.get() - 10.0) * 2.0) + \
                                ((self.super_tax_rate.get() - 15.0) * 1.0) + \
                                ((self.fuel_excise_rate.get() - 44.0) * 0.3) + \
                                ((self.small_business_tax.get() - 25.0) * 0.3)

        fac_rev, fac_upkeep, total_fac_workers = 0.0, 0.0, 0
        labor_tightness = max(0.8, 1.2 - (self.unemployment - 3.5) * 0.05)

        iron_levy = self.resource_levies["Iron (Raw Material)"].get()
        smelter_profit_modifier = 0.5 if iron_levy <= 15.0 else 1.2

        for res, data in self.facilities.items():
            count = data["count"]
            rev = data["rev"]

            if res == "Iron Ore Smelter":
                rev *= smelter_profit_modifier

            fac_rev += count * rev
            fac_upkeep += count * (data["upkeep"] * labor_tightness)
            total_fac_workers += count * data["workers"]

        if "China" in self.defeated_countries:
            fac_upkeep *= 0.5
            fac_rev *= 1.5

        # EXPLICIT LEVY REVENUES (Peak at 15%, drop to 0 at higher rates)
        def eff_rev(rate):
            return rate if rate <= 15.0 else max(0.0, 30.0 - rate)

        num_iron_smelters = self.facilities["Iron Ore Smelter"]["count"]
        steel_levy_eff = eff_rev(self.resource_levies["Steel"].get())

        if iron_levy <= 15.0 and num_iron_smelters < 3:
            steel_levy_revenue = steel_levy_eff * 0.01
        else:
            steel_levy_revenue = steel_levy_eff * 0.10 * num_iron_smelters

        crude_oil_levy_eff = eff_rev(self.resource_levies["Crude Oil"].get())
        petrol_levy_eff = eff_rev(self.resource_levies["Petrol"].get())
        diesel_levy_eff = eff_rev(self.resource_levies["Diesel"].get())
        beef_levy_eff = eff_rev(self.resource_levies["Beef"].get())
        num_oil_fields = self.facilities["Oil Extraction Field"]["count"]
        num_offshore_rigs = self.facilities["Offshore Oil Rig"]["count"]
        num_oil_refineries = self.facilities["Oil Refinery"]["count"]

        base_crude_revenue = (num_oil_fields + num_offshore_rigs) * (crude_oil_levy_eff * 0.05)
        if "Russia" in self.defeated_countries:
            base_crude_revenue *= 2.0

        refinery_bonus_revenue = num_oil_refineries * (crude_oil_levy_eff * 0.075)
        total_crude_revenue = base_crude_revenue + refinery_bonus_revenue

        petrol_levy_revenue = petrol_levy_eff * 0.05 * num_oil_refineries
        diesel_levy_revenue = diesel_levy_eff * 0.05 * num_oil_refineries
        beef_levy_revenue = beef_levy_eff * 0.15 # Baseline agricultural output tax

        ram_levy_rev = 0.0
        if self.facilities["RAM Production Plant"]["count"] > 0:
            ram_levy_rev = eff_rev(self.resource_levies["RAM (Req. Plant)"].get()) * 0.08

        zircon_levy_rev = 0.0
        if self.facilities["Zirconium Refinery"]["count"] > 0:
            zircon_levy_rev = eff_rev(self.resource_levies["Zirconium"].get()) * 0.09

        zinc_levy_rev = 0.0
        if self.facilities["Zinc Refinery"]["count"] > 0:
            zinc_levy_rev = eff_rev(self.resource_levies["Zinc"].get()) * 0.07

        nickel_levy_rev = 0.0
        if self.facilities["Nickel Refinery"]["count"] > 0:
            nickel_levy_rev = eff_rev(self.resource_levies["Nickel"].get()) * 0.08

        tungsten_levy_rev = 0.0
        if self.facilities["Tungsten Refinery"]["count"] > 0:
            tungsten_levy_rev = eff_rev(self.resource_levies["Tungsten"].get()) * 0.09

        excluded_levies = ["RAM (Req. Plant)", "Zirconium", "Iron (Raw Material)", "Steel", "Crude Oil", "Petrol", "Diesel", "Beef", "Zinc", "Nickel", "Tungsten"]
        generic_levy_rev = sum(eff_rev(v.get()) * 0.08 for k, v in self.resource_levies.items() if k not in excluded_levies)

        iron_levy_rev = eff_rev(iron_levy) * 0.08

        export_levy_rev = generic_levy_rev + ram_levy_rev + zircon_levy_rev + zinc_levy_rev + nickel_levy_rev + tungsten_levy_rev + steel_levy_revenue + total_crude_revenue + petrol_levy_revenue + diesel_levy_revenue + beef_levy_revenue + iron_levy_rev

        if getattr(self, 'nuclear_sanctions', False):
            export_levy_rev = 0.0

        tariff_rev = sum(v.get() for v in self.tariffs.values()) * 0.12

        # New Taxes Revenues
        w_tax = self.annual_wealth_tax.get()
        tax_rev += w_tax * 0.1

        ftt = self.fin_trans_tax.get()
        tax_rev += ftt * 0.5

        tax_rev += self.luxury_car_tax.get() * 0.005

        m_levy = self.medicare_levy.get()
        infra_levy = self.infrastructure_levy.get()
        tax_rev += m_levy * 0.4
        tax_rev += infra_levy * 2.0

        total_revenue = tax_rev + fac_rev + export_levy_rev + tariff_rev + rev_impact

        if getattr(self, 'net_zero_accepted', False):
            total_revenue -= 2.0

        # Shale Oil Boom
        if getattr(self, 'shale_boom_timer', 0) > 12:
            total_revenue -= 0.5
        elif getattr(self, 'shale_boom_timer', 0) > 0:
            total_revenue += 3.0

        # Aged care revenue impact
        aged_diff = self.aged_care_cover.get() - 70.0
        if aged_diff > 0:
            total_revenue -= aged_diff * 0.02
        elif aged_diff < 0:
            total_revenue += abs(aged_diff) * 0.02

        # Apply active recession modifier to revenue
        if self.recession_active:
            total_revenue -= 10.0

        law_inflation_mod = 0.0
        for info in self.laws.values():
            if info["passed"]:
                if "rev_add" in info: total_revenue += info["rev_add"]
                if "cost" in info: total_revenue -= info["cost"]
                if "infl_mod" in info: law_inflation_mod += info["infl_mod"]

        if self.carbon_sanctions_active:
            total_revenue -= 10.0

        if self.is_at_war: total_revenue *= 0.65

        if self.foreign_relations <= 0.0:
            total_revenue -= 3.0
        elif self.foreign_relations >= 100.0:
            total_revenue += 2.0

        # Spoils of War Revenue Expansion
        spoils_revenue = 0.0
        for nation in self.defeated_countries:
            if nation in ["PNG", "Fiji", "New Zealand", "Solomon Islands"]:
                spoils_revenue += 2.0
            elif nation in ["Philippines", "Japan", "Taiwan", "Indonesia"]:
                spoils_revenue += 5.0
            elif nation in ["United States", "Russia", "China", "India"]:
                spoils_revenue += 10.0
        total_revenue += spoils_revenue

        eff_age_pension = self.age_pension.get() * (4.5 / 1200.0)
        eff_family_benefits = self.family_benefits.get() * (1.6 / 300.0)
        welfare_total = eff_age_pension + self.ndis_spend.get() + self.jobseeker.get() + eff_family_benefits

        public_spending = self.health_spend.get() + self.police_spend.get() + welfare_total + \
                          self.defence_spend.get() + self.education_spend.get() + self.infra_spend.get() + \
                          self.housing_spend.get() + self.foreign_aid.get() + \
                          self.arts_funding.get() + self.env_spend.get() + \
                          (self.climate_spend.get() / 12.0) + (self.net_zero_spend.get() / 12.0)

        debt_interest = (max(0, self.debt) * 0.035) / 12.0

        total_spending = public_spending + fac_upkeep + debt_interest + self.structural_fixed_costs
        self.monthly_balance = total_revenue - total_spending

        profit_happy_modifier = 0.0
        profit_inflation_modifier = 0.0
        if self.monthly_balance > 0:
            profit_happy_modifier = min(5.0, self.monthly_balance * 1.5)
            profit_inflation_modifier = max(-2.0, self.monthly_balance * -0.2)
            self.senate_popularity = min(100, self.senate_popularity + 0.5)
        elif self.monthly_balance < 0:
            profit_happy_modifier = max(-8.0, self.monthly_balance * 2.0)
            profit_inflation_modifier = min(3.0, abs(self.monthly_balance) * 0.3)
            self.senate_popularity = max(0, self.senate_popularity - 0.5)

        gas_plant_penalty = 0.0
        gas_plant_discount = 0.0
        if open_cycle > 0:
            if open_cycle > oil_gas_plants:
                gas_plant_penalty = (open_cycle - oil_gas_plants) * 2.0
            else:
                gas_plant_discount = open_cycle * 2.0

        tax_inflation_penalty = ((self.fuel_excise_rate.get() - 44.0) * 0.05) + ((self.gst_rate.get() - 10.0) * 0.1)
        debt_inflation_penalty = max(0.0, (self.debt - 1000.0) / 500.0) * 1.0

        # Spending & Procurements Inflation Rule: Every $15 billion spent is 0.20% inflation
        active_procurement_cost = sum(p["cost"] for p in self.active_procurements)
        total_annual_spending_calc = (public_spending * 12.0) + active_procurement_cost
        spending_procurement_inflation = (total_annual_spending_calc / 15.0) * 0.20

        levy_inflation_reduction = 0.0
        refinery_map = {
            "Crude Oil": "Oil Refinery",
            "Petrol": "Oil Refinery",
            "Diesel": "Oil Refinery",
            "Iron (Raw Material)": "Iron Ore Smelter",
            "Steel": "Iron Ore Smelter",
            "Gold": "Gold Refinery",
            "Lithium": "Lithium Processing Plant",
            "Rare Earths": "Rare Earths Refinery",
            "Copper": "Copper Smelting Plant",
            "Uranium": "Uranium Mine",
            "RAM (Req. Plant)": "RAM Production Plant",
            "Zirconium": "Zirconium Refinery",
            "Zinc": "Zinc Refinery",
            "Nickel": "Nickel Refinery",
            "Tungsten": "Tungsten Refinery"
        }
        for res, var in self.resource_levies.items():
            val = var.get()
            if val > 0:
                fac = refinery_map.get(res)
                if fac and self.facilities.get(fac, {}).get("count", 0) >= 2:
                    levy_inflation_reduction += val * 0.10
                else:
                    levy_inflation_reduction += val * 0.02

        base_infl = 2.0 + infl_impact + (sum(v.get() for v in self.tariffs.values()) * 0.08) + \
                    profit_inflation_modifier + law_inflation_mod + self.event_inflation_mod + \
                    tax_inflation_penalty - (nuke_count * 0.3) - (coal_count * 0.1) + \
                    (gas_plant_penalty * 0.5) + debt_inflation_penalty - levy_inflation_reduction + \
                    spending_procurement_inflation

        if cgt_val > 50.0:
            base_infl += ((cgt_val - 50.0) / 50.0) * 1.2

        base_infl -= (fbt_val_rate / 100.0) * 2.0

        if self.climate_spend.get() <= 0.1 and self.net_zero_spend.get() <= 0.1:
            base_infl -= 2.5

        if self.tariffs_timer > 0: base_infl += 5.0
        if self.sanctions_active: base_infl += 15.0

        if self.carbon_sanctions_active:
            base_infl += 8.0

        if self.is_at_war: base_infl += 10.0

        if self.foreign_relations <= 0.0:
            base_infl += 10.0
        elif self.foreign_relations >= 100.0:
            base_infl -= 1.0

        # Health & Medicare Inflation Rule
        health_val = self.health_spend.get()
        if health_val < 8.5:
            base_infl += (8.5 - health_val) * 0.5
        elif health_val > 8.5:
            base_infl -= (health_val - 8.5) * 0.2

        self.inflation = base_infl

        # Average interest rate follows inflation and is capped by the Interest Rate Cap Act if passed.
        if self.laws.get("Interest Rate Cap Act", {}).get("passed"):
            cap_limit = 4.5 if self.interest_cap_override is None else self.interest_cap_override
            self.avg_interest_rate = max(0.8, min(cap_limit, 6.20 + ((self.inflation - 2.8) * 0.60)))
        else:
            self.interest_cap_override = None
            self.avg_interest_rate = max(2.0, min(9.4, 6.20 + ((self.inflation - 2.8) * 0.60)))
            if self.avg_interest_rate < 4.5:
                self.inflation -= 0.25
                if self.avg_interest_rate < 4.0:
                    self.inflation -= 0.35
                if self.avg_interest_rate < 3.0:
                    self.inflation -= 0.45
                self.avg_interest_rate = max(2.0, min(4.5, 6.20 + ((self.inflation - 2.8) * 0.60)))

        # Calculate live commodity market prices
        self.update_market_calculations()

        # Interconnected Market Impacts on Power Bills
        petrol_mkt = self.market_prices["Petrol"]["current"]
        diesel_mkt = self.market_prices["Diesel"]["current"]
        uran_mkt = self.market_prices["Uranium"]["current"]
        lith_mkt = self.market_prices["Lithium"]["current"]
        lng_mkt = self.market_prices["LNG"]["current"]
        zinc_mkt = self.market_prices["Zinc"]["current"]
        nickel_mkt = self.market_prices["Nickel"]["current"]
        copper_mkt = self.market_prices["Copper"]["current"]

        power_mkt_impact = 0.0
        if solar_count > 0:
            power_mkt_impact += (lith_mkt - 25.0) * 0.4 * solar_count
        if nuke_count > 0:
            power_mkt_impact += (uran_mkt - 180.0) * 0.05 * nuke_count
        if open_cycle > 0:
            power_mkt_impact += (lng_mkt - 0.70) * 15.0 * open_cycle + (petrol_mkt - 2.00) * 5.0 * open_cycle

        power_mkt_impact += (zinc_mkt - 4.0) * 0.5 + (nickel_mkt - 20.0) * 0.2 + (copper_mkt - 14.0) * 0.3

        base_power = 120.0 + (self.inflation * 3.0) - (nuke_count * 5.0) - (coal_count * 8.0) - (combined_cycle * 5.0) - gas_plant_discount + gas_plant_penalty - (flood_plants * 1.0) + (desal_plants * 5.0) + (data_centers * 5.0) + power_mkt_impact

        if self.laws.get("Pass Hydrogen Bus Bill", {}).get("passed") and open_cycle >= 2:
            base_power -= 10.0

        self.power_bills = max(40.0, base_power)

        if getattr(self, 'net_zero_accepted', False):
            self.power_bills += 15.0

        if hasattr(self, 'net_zero_grid_penalty'):
            self.power_bills += self.net_zero_grid_penalty

        # Electricity Market Calculation
        self.market_prices["Electricity"]["current"] = max(5.0, (self.power_bills / 120.0) * 25.0)
        self.market_prices["Electricity"]["factors"] = "Tied to National Power Grid"
        electricity_base_price = max(float(self.market_prices["Electricity"]["base"]), 0.000001)
        electricity_current_price = max(float(self.market_prices["Electricity"]["current"]), 0.000001)
        electricity_demand_ratio = max(0.5, min(1.5, (electricity_base_price / electricity_current_price) ** 0.5))
        self.market_prices["Electricity"]["demand"] = min(100.0, self.market_prices["Electricity"].get("base_demand", 100.0) * electricity_demand_ratio)
        self.update_market_table()

        try:
            if self.prog_power.winfo_exists():
                self.prog_power['value'] = self.power_bills
            if self.lbl_power.winfo_exists():
                self.lbl_power.config(text=f"${self.power_bills:.0f}/mo AUD")
        except tk.TclError:
            pass
        power_bill_penalty = max(0, (self.power_bills - 100) * 0.15)
        power_bill_bonus = math.floor(max(0.0, 120.0 - self.power_bills) / 15.0) * 5.0

        labor_force = (self.population * 0.62) + monthly_immig
        unemp_mod_taxes = ((fbt_val_rate - 47.0) * 0.4) + ((cgt_val_rate - 25.0) * 0.05)

        # Payroll & Wealth Tax Rule
        payroll_unemp_mod = (self.payroll_tax.get() - 5.0) * 0.8
        w_tax_unemp_penalty = self.annual_wealth_tax.get() * 0.25

        self.unemployment = max(1.8, min(40.0, 100.0 * (1.0 - ((int(public_spending * 12_000) + total_fac_workers + self.base_private_jobs) / labor_force))))
        self.unemployment = max(1.8, self.unemployment + unemp_mod_taxes + payroll_unemp_mod + self.event_unemployment_mod + w_tax_unemp_penalty)

        # Apply active recession modifier to unemployment
        if self.recession_active:
            self.unemployment += 10.0

        if self.foreign_relations <= 0.0:
            self.unemployment += 5.0

        # RECESSION RECOVERY LOCK
        if getattr(self, 'recession_recovery_timer', 0) > 0:
            self.unemployment = 4.0

        self.health_index = max(10, min(100, 50 + (self.health_spend.get() * 1.5) + self.event_health_mod))
        defense_security_bonus = sum(data["count"] for name, data in self.facilities.items() if data["type"] == "Defense") * 2.5

        self.crime_index = max(10, min(100, 70 - (self.police_spend.get() * 4.5) + (self.unemployment * 1.5) - defense_security_bonus + immig_crime_impact + self.event_crime_mod + sin_crime_impact))

        for info in self.laws.values():
            if info["passed"]:
                if "health_bonus" in info: self.health_index = min(100, self.health_index + info["health_bonus"])
                if "crime_sub" in info: self.crime_index = max(10, self.crime_index - info["crime_sub"])
                if "crime_add" in info: self.crime_index = min(100, self.crime_index + info["crime_add"])

        try:
            if self.prog_crime.winfo_exists():
                self.prog_crime['value'] = self.crime_index
            if self.lbl_crime.winfo_exists():
                self.lbl_crime.config(text=f"{self.crime_index:.1f}/100", fg="#FF6666" if self.crime_index > 50 else "white")
        except tk.TclError:
            pass

        # Market Price Happiness Cross-Effect
        petrol_happy_impact = (2.00 - petrol_mkt) * 6.0
        water_happy_impact = (0.003 - self.market_prices["Water"]["current"]) * 1000.0

        # Adjust inflation happiness penalty
        infl_happiness_penalty = 0.0
        if self.inflation > 3.0:
            infl_happiness_penalty = self.inflation * 3.5
        elif self.inflation < -1.0:
            infl_happiness_penalty = abs(self.inflation) * 3.5

        # New Tax and Variable Happiness Impacts
        if aged_diff > 0:
            happy_impact += aged_diff * 0.15
        elif aged_diff < 0:
            happy_impact -= abs(aged_diff) * 2.0

        if m_levy > 2.0:
            happy_impact -= (m_levy - 2.0) * 3.0
        elif m_levy < 1.7:
            happy_impact -= (1.7 - m_levy) * 15.0
        elif 1.7 <= m_levy <= 2.0:
            if 1.8 <= m_levy <= 1.9:
                happy_impact += 3.0

        infrastructure_happy_modifier = 0.0
        if abs(infra_levy - 0.5) < 0.001:
            infrastructure_happy_modifier = 2.0
        elif infra_levy > 0.5:
            infrastructure_happy_modifier = -(infra_levy - 0.5) * 8.0
        happy_impact += infrastructure_happy_modifier

        happy_impact -= ftt * 4.0
        happy_impact -= w_tax * 1.5

        wcpi = self.wage_cpi_index.get()
        if wcpi < 0.0:
            happy_impact -= (abs(wcpi) / 0.5) * 15.0
        else:
            if wcpi <= 1.5:
                happy_impact += (wcpi / 1.5) * 8.0
            else:
                happy_impact += 8.0
                happy_impact -= ((wcpi - 1.5) / 0.5) * 10.0

        interest_happy_modifier = 0.0
        if self.avg_interest_rate > 7.0:
            interest_happy_modifier -= min(18.0, (self.avg_interest_rate - 7.0) * 8.0)
        elif self.avg_interest_rate < 4.0:
            interest_happy_modifier += min(18.0, (4.0 - self.avg_interest_rate) * 12.0)
        if self.laws.get("Interest Rate Cap Act", {}).get("passed"):
            interest_happy_modifier += 15.0

        self.happiness = 70.0 + (self.health_index * 0.25) - (self.crime_index * 0.35) - \
                         infl_happiness_penalty - ((self.unemployment - 4.0) * 3.0) + happy_impact + \
                         (welfare_total * 0.3) - power_bill_penalty + power_bill_bonus + \
                         profit_happy_modifier + self.event_happy_mod - tax_happiness_penalty - (gas_plant_penalty * 0.5) + \
                          petrol_happy_impact + water_happy_impact + interest_happy_modifier

        if self.tariffs_timer > 0: self.happiness -= 3.0
        elif self.tariffs_boost_active: self.happiness += 2.0
        if self.sanctions_active: self.happiness -= 3.0

        for info in self.laws.values():
            if info["passed"] and "happy_bonus" in info: self.happiness += info["happy_bonus"]

        if self.is_at_war: self.happiness -= 15.0

        if self.inflation < 0:
            self.happiness += 10.0

        # Age Pension & Family Tax Happiness Rule
        age_diff = eff_age_pension - 4.5
        fam_diff = eff_family_benefits - 1.6

        if age_diff < 0:
            self.happiness -= abs(age_diff) * 35.0
        else:
            self.happiness += age_diff * 5.0

        if fam_diff < 0:
            self.happiness -= abs(fam_diff) * 35.0
        else:
            self.happiness += fam_diff * 5.0

        # Health & Medicare Happiness Rule (Decreases by 50% per $2B under $8.5B)
        if health_val < 8.5:
            self.happiness -= ((8.5 - health_val) / 2.0) * 50.0

        # Invisible Buffer Fix & Strict Caps
        if self.happiness > 100.0:
            excess = self.happiness - 100.0
            self.event_happy_mod -= excess
            self.happiness = 100.0

        self.happiness = max(5.0, min(100.0, round(self.happiness, 1)))

        # Cap happiness at 85% if crime is above 40
        if self.crime_index > 40.0 and self.happiness > 85.0:
            self.happiness = 85.0

        # Cap happiness at 70% if unemployment exceeds 12%
        if self.unemployment > 12.0 and self.happiness > 70.0:
            self.happiness = 70.0

        # RECESSION RECOVERY LOCK
        if getattr(self, 'recession_recovery_timer', 0) > 0:
            self.happiness = max(self.happiness, 70.0)

        # Cap happiness at 80% for GST/Tax/Infl limits
        if self.happiness > 80.0:
            if self.gst_rate.get() > 20.0 or \
               self.tax_bracket_15.get() >= 24.0 or \
               self.tax_bracket_30.get() >= 35.0 or \
               self.tax_bracket_37.get() >= 42.0 or \
               self.tax_bracket_45.get() >= 50.0 or \
               self.inflation > 8.0 or \
               self.inflation < -3.0:
                self.happiness = 80.0

        bal_str = f"+${self.monthly_balance:.2f}B AUD/mo" if self.monthly_balance >= 0 else f"-${abs(self.monthly_balance):.2f}B AUD/mo"

        try:
            if self.lbl_balance.winfo_exists():
                self.lbl_balance.config(text=bal_str, fg="#00FF66" if self.monthly_balance >= 0 else "#FF6666")

            if self.debt > 0:
                if self.lbl_debt.winfo_exists():
                    self.lbl_debt.config(text=f"${self.debt:.1f}B AUD", fg="#FF6666")
            else:
                if self.lbl_debt.winfo_exists():
                    self.lbl_debt.config(text=f"+${abs(self.debt):.1f}B AUD (Surplus)", fg="#00FF66")

            if self.lbl_happiness.winfo_exists():
                self.lbl_happiness.config(text=f"{self.happiness:.1f}%")
            if self.lbl_unemp.winfo_exists():
                self.lbl_unemp.config(text=f"{self.unemployment:.1f}%")
            if self.lbl_inflation.winfo_exists():
                self.lbl_inflation.config(text=f"{self.inflation:.1f}%", fg="white")
            if self.lbl_interest.winfo_exists():
                self.lbl_interest.config(text=f"{self.avg_interest_rate:.1f}%")
        except tk.TclError:
            pass

    def check_random_events(self):
        if self.events_this_term >= self.max_events_this_term:
            # Check guaranteed trigger conditions even if max events reached
            return self.check_guaranteed_triggers()

        # Regular random events checks
        if self.check_guaranteed_triggers():
            return True

        tariffed_countries = [c.split(" -")[0] for c, v in self.tariffs.items() if v.get() > 0]
        if tariffed_countries and self.calculate_military_score() < 12.0 and random.random() < 0.04:
            attacker = "China"
            self.trigger_invasion(attacker, 2)
            self.events_this_term += 1
            return True

        if not self.bondi_event_occurred and self.immigration_policy.get() in ["High (75k/mo)", "Massive Open (150k/mo)"] and self.crime_index > 50:
            if random.random() < 0.20:
                self.trigger_bondi_event()
                self.events_this_term += 1
                return True

        lng = self.facilities["LNG Processing Facility"]["count"]
        oil_refineries = self.facilities["Oil Refinery"]["count"]

        fuel_blocked = (oil_refineries >= 10) or (lng >= 10)

        if not self.fuel_crisis_occurred and random.random() < 0.05 and not fuel_blocked:
            self.fuel_crisis_occurred = True
            self.trigger_fuel_crisis()
            self.events_this_term += 1
            return True

        if not self.oil_spill_prevented and self.facilities["Offshore Oil Rig"]["count"] > 2 and random.random() < 0.10:
            self.trigger_oil_spill()
            self.events_this_term += 1
            return True

        cyber_blocked = (self.facilities["Data Center"]["count"] >= 3)
        if self.is_at_war and not cyber_blocked and random.random() < 0.05:
            self.trigger_standard_event({"name": "Major Cyber Attack", "desc": "Enemy state hackers have crippled critical infrastructure!", "cost": 4.0, "penalties": {"happy": -12, "crime": 10}})
            self.events_this_term += 1
            return True

        drought_blocked = (self.facilities["Desalination Plant"]["count"] > 10)
        if not drought_blocked and random.random() < 0.06:
            self.trigger_standard_event({"name": "Severe National Drought", "desc": "A catastrophic drought is ravaging the agricultural sector.", "cost": 3.0, "penalties": {"happy": -10, "health": -5}})
            self.events_this_term += 1
            return True

        if random.random() > 0.15 and not self.force_market_crash:
            return False

        possible_events = []
        possible_events.append({"name": "Crime Spree in Alice Springs"})
        possible_events.append({"name": "Crime Spree in Melbourne"})

        if self.education_spend.get() < 4.0:
            possible_events.append({"name": "Youth Crime Spree (Underfunded Education)"})

        low_immig = self.immigration_policy.get() in ["Closed Borders (0/mo)", "Low (15k/mo)"]
        laws_active = self.laws["Block Foreign Property Purchases"]["passed"] or self.laws["Strip Councils of House Blocking"]["passed"]

        if not ((self.housing_crisis_blocked_until > self.term_month) or (low_immig and laws_active)):
            possible_events.append({"name": "Severe Housing Crisis"})

        if self.facilities["Flood-Catchment Plant"]["count"] <= 12:
            possible_events.append({"name": "Major Regional Floods"})

        if self.month in [11, 12, 1, 2]:
            possible_events.append({"name": "Catastrophic Bushfires"})

        possible_events.append({"name": "Global Pandemic"})
        possible_events.append({"name": "Financial Market Crash"})
        possible_events.append({"name": "Supply Chain Collapse"})

        if not self.net_zero_push_occurred:
            possible_events.append({"name": "Global Net Zero Push"})

        # Grid Failure conditional check
        nuke_count = self.facilities["Nuclear Power Plant"]["count"]
        gas_count = self.facilities["Open-Cycle Gas Plant"]["count"]
        combined_gas_count = self.facilities["Combined Cycle Gas Plant"]["count"]
        coal_count = self.facilities["Coal Power Plant"]["count"]
        grid_failure_protected = (gas_count >= 2) or (combined_gas_count >= 2 and coal_count >= 2) or (nuke_count >= 2)
        if not grid_failure_protected:
            if getattr(self, 'net_zero_accepted', False) == True:
                possible_events.extend([{"name": "National Grid Failure"}] * 3)
            elif getattr(self, 'net_zero_accepted', None) == False:
                if random.random() < 0.3:
                    possible_events.append({"name": "National Grid Failure"})
            else:
                possible_events.append({"name": "National Grid Failure"})

        if self.debt > 0 or self.monthly_balance < 0:
            possible_events.append({"name": "Sovereign Debt Downgrade Threat"})

        if self.facilities.get("RAM Production Plant", {}).get("count", 0) == 0:
            possible_events.append({"name": "RAM Shortage"})

        if self.force_market_crash:
            chosen_name = "Financial Market Crash"
            self.force_market_crash = False
            self.laws["Illigalise Santanism"]["passed"] = False
            self.render_laws()
        else:
            chosen_event = random.choice(possible_events)
            chosen_name = chosen_event["name"] if isinstance(chosen_event, dict) else chosen_event

        if chosen_name == "Crime Spree in Alice Springs":
            self.trigger_crime_spree("Alice Springs")
        elif chosen_name == "Crime Spree in Melbourne":
            self.trigger_crime_spree("Melbourne")
        elif chosen_name == "Youth Crime Spree (Underfunded Education)":
            self.trigger_youth_crime_spree()
        elif chosen_name == "Catastrophic Bushfires":
            self.trigger_bushfire()
        elif chosen_name == "Severe Housing Crisis":
            self.trigger_standard_event({"name": "Severe Housing Crisis", "desc": "Record low vacancy rates are driving up homelessness rapidly. Will you fast-track emergency social housing?", "cost": 4.0, "penalties": {"happy": -10}})
        elif chosen_name == "Major Regional Floods":
            flood_plants = self.facilities["Flood-Catchment Plant"]["count"]
            flood_reduction_chance = min(0.15, flood_plants * 0.015)
            if random.random() < flood_reduction_chance:
                messagebox.showinfo("Disaster Averted", "Heavy rains struck the eastern seaboard, but your Flood-Catchment Plants successfully prevented the major regional floods!")
                self.events_this_term += 1
                return True
            else:
                self.trigger_standard_event({"name": "Major Regional Floods", "desc": "Devastating floods have destroyed homes and infrastructure across the eastern seaboard.", "cost": 2.5, "penalties": {"health": -5, "happy": -8}})
        elif chosen_name == "Global Net Zero Push":
            self.trigger_net_zero_push()
        elif chosen_name == "Global Pandemic":
            self.trigger_pandemic()
        elif chosen_name == "Financial Market Crash":
            self.trigger_market_crash()
        elif chosen_name == "Supply Chain Collapse":
            self.trigger_supply_collapse()
        elif chosen_name == "National Grid Failure":
            self.trigger_grid_failure()
        elif chosen_name == "Sovereign Debt Downgrade Threat":
            self.trigger_debt_downgrade()
        elif chosen_name == "RAM Shortage":
            self.trigger_ram_shortage()

        self.events_this_term += 1
        return True

    def check_guaranteed_triggers(self):
        # 0. Bigot Event
        if getattr(self, 'immigration_zero_months', 0) >= 2 and not getattr(self, 'bigot_event_occurred', False):
            self.bigot_event_occurred = True
            self.trigger_bigot_event()
            return True

        # 1. Trade War (Zirconium Levy > 0%)
        if self.resource_levies["Zirconium"].get() > 0.0 and not self.trade_war_event_occurred:
            if self.war_opponent != "China" and "China" not in self.defeated_countries:
                self.trade_war_event_occurred = True
                self.trigger_trade_war()
                return True

        # 2. Recession Event
        low_immig = self.immigration_policy.get() in ["Closed Borders (0/mo)", "Low (15k/mo)"]
        if not self.recession_active and (self.inflation < -5.0 or (self.inflation < 0.0 and low_immig)):
            self.recession_active = True
            self.trigger_recession()
            return True

        # Reset Unemployment event if below threshold so it can trigger again
        if self.unemployment <= 10.0:
            self.unemployment_event_occurred = False

        # 3. High Unemployment Event
        if self.unemployment > 10.0 and not self.unemployment_event_occurred:
            self.unemployment_event_occurred = True
            self.trigger_unemployment_crisis()
            return True

        # 4. Black Market Event
        if self.sin_tax.get() > 50.0 and self.crime_index > 20.0 and not getattr(self, 'black_market_occurred', False):
            if random.random() < 0.05:
                self.black_market_occurred = True
                self.trigger_black_market()
                return True

        # 5. Investment Pullout Event
        if self.laws.get("Interest Rate Cap Act", {}).get("passed") and self.avg_interest_rate < 2.0 and not getattr(self, 'investment_pullout_occurred', False):
            if random.random() < 0.10:
                self.investment_pullout_occurred = True
                self.trigger_investment_pullout()
                return True

        # 6. Shale Oil Event
        if self.facilities["Oil Extraction Field"]["count"] >= 2 and self.total_months_played > 26 and not getattr(self, 'shale_oil_occurred', False):
            if random.random() < 0.05:
                self.shale_oil_occurred = True
                self.trigger_shale_oil()
                return True

        return False

    def trigger_bigot_event(self):
        def ignore():
            self.senate_popularity = max(0.0, self.senate_popularity + 0.0)

        def woke():
            self.event_happy_mod += 5.0
            self.senate_popularity = min(100.0, self.senate_popularity + 5.0)

        def whine():
            self.event_happy_mod -= 5.0

        self.show_overlay("BIGOT 🫵🏿", "The Greens have publicly called you a Bigot for closing the borders.", "#00843D",
            [("Ignore", ignore, "#CCCCCC"),
             ("Call them Woke Nut jobs", woke, "#002B49"),
             ("whine on the ABC", whine, "#D9381E")])

    def trigger_investment_pullout(self):
        def ignore():
            self.property_price_index += 25.0
            self.event_inflation_mod += 8.0
            self.event_happy_mod -= 10.0
            self.senate_popularity = max(0.0, self.senate_popularity - 10.0)
            self.recent_news.append("Banks stop approving new loans as investment capital pulls out; property prices rise sharply and inflation surges.")

        def raise_cap():
            self.interest_cap_override = 6.0
            self.property_price_index += 5.0
            self.event_inflation_mod += 1.0
            self.event_happy_mod += 2.0
            self.senate_popularity = min(100.0, self.senate_popularity + 4.0)
            self.recent_news.append("The interest-rate cap is raised to 6.0%, restoring bank lending and stopping the investment-driven property surge.")

        def remove_cap():
            self.laws["Interest Rate Cap Act"]["passed"] = False
            self.interest_cap_override = None
            self.property_price_index += 10.0
            self.event_inflation_mod += 3.0
            self.event_happy_mod -= 4.0
            self.senate_popularity = max(0.0, self.senate_popularity - 4.0)
            self.render_laws()
            self.recent_news.append("The interest-rate cap has been removed, allowing lending rates to reset while the investment shock eases.")

        self.show_overlay(
            "⚠️ INVESTMENT PULLOUT",
            "Banks have sharply restricted lending after interest rates fell below 2.0% under the interest-rate cap. Investment capital is leaving, property prices are rising and inflation is accelerating.",
            "#8B0000",
            [
                ("Ignore", ignore, "#CCCCCC"),
                ("Raise Cap to 6%", raise_cap, "#00843D"),
                ("Remove Cap", remove_cap, "#002B49")
            ]
        )

    def trigger_trade_war(self):
        def ignore():
            self.event_inflation_mod += 3.0
            self.senate_popularity = max(0.0, self.senate_popularity - 5.0)

        def remove_levy():
            self.resource_levies["Zirconium"].set(0.0)
            self.trade_war_event_occurred = False # Can be triggered again if they raise it back up
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        options = [
            ("Stand Firm (Ignore Threat) [+3% Inflation]", ignore, "#002B49"),
            ("Remove Zirconium Levy Immediately", remove_levy, "#00843D")
        ]

        if self.foreign_relations >= 100.0:
            def call_ally():
                self.trade_war_event_occurred = False
                self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
                self.event_inflation_mod -= 1.0
            options.append(("Call for Ally Help", call_ally, "#FFC72C"))

        self.show_overlay(
            "⚠️ TRADE WAR",
            "China needs Zirconium for their defense force and will fight for it. They are furious about your export levy and have threatened severe economic retaliation.",
            "#D9381E",
            options
        )

    def trigger_unemployment_crisis(self):
        def ignore():
            self.event_happy_mod -= 10.0
            self.senate_popularity = max(0.0, self.senate_popularity - 10.0)

        def small_relief():
            self.debt += 3.0
            self.event_inflation_mod += 1.5
            self.event_unemployment_mod -= 3.0
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def huge_program():
            self.debt += 50.0
            self.event_inflation_mod += 5.0
            self.event_unemployment_mod -= 8.5
            self.senate_popularity = min(100.0, self.senate_popularity + 8.0)

        self.show_overlay(
            "⚠️ MASS UNEMPLOYMENT CRISIS",
            "Unemployment has exceeded 10.0%. The nation is suffering from severe joblessness and public unrest is growing rapidly.",
            "#D9381E",
            [
                ("Ignore Crisis", ignore, "#CCCCCC"),
                ("Targeted Relief ($3.0B AUD)", small_relief, "#002B49"),
                ("Massive Job Opportunity Program ($50.0B AUD)", huge_program, "#00843D")
            ]
        )

    def trigger_crime_spree(self, location):
        def fund_relief():
            self.debt += 0.5
            self.event_inflation_mod += 0.25
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def ignore():
            self.event_crime_mod += 15
            self.event_happy_mod -= 5
            self.senate_popularity = max(0.0, self.senate_popularity - 5.0)

        def deploy_adf():
            self.debt += 5.0
            self.event_crime_mod -= 45
            self.senate_popularity = min(100.0, self.senate_popularity + 5.0)

        self.show_overlay(
            f"⚠️ CRIME SPREE IN {location.upper()}",
            f"A massive youth crime wave has hit {location}. How do you respond?",
            "#D9381E",
            [
                ("Fund Police Relief ($0.5B AUD)", fund_relief, "#00843D"),
                (f"Deploy ADF to {location} ($5.0B AUD)", deploy_adf, "#002B49"),
                ("Ignore Crisis", ignore, "#CCCCCC")
            ]
        )

    def trigger_youth_crime_spree(self):
        def fund():
            self.debt += 1.0
            self.event_inflation_mod += 1.5
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def deploy_adf():
            self.debt += 5.0
            self.event_crime_mod -= 10.0
            self.event_happy_mod += 5.0
            self.senate_popularity = min(100.0, self.senate_popularity + 5.0)

        def ignore():
            self.event_happy_mod -= 10.0
            self.event_crime_mod += 10.0
            self.senate_popularity = max(0.0, self.senate_popularity - 5.0)

        self.show_overlay("⚠️ YOUTH CRIME SPREE", "Education funding has dropped below critical levels, triggering a massive youth crime wave across multiple cities.", "#D9381E",
            [("Fund Relief ($1.0B AUD, Infl +1.5%)", fund, "#00843D"),
             ("Deploy ADF ($5.0B AUD, Happy +5%, Crime -10)", deploy_adf, "#002B49"),
             ("Ignore (Happy -10%, Crime +10)", ignore, "#CCCCCC")])

    def trigger_bushfire(self):
        def pay():
            self.debt += 3.0
            self.event_inflation_mod += 1.5
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def rain_catchment():
            self.debt += 3.0
            self.senate_popularity = min(100.0, self.senate_popularity + 3.0)

        def ignore():
            self.event_health_mod -= 8
            self.event_happy_mod -= 12
            self.senate_popularity = max(0.0, self.senate_popularity - 5.0)

        options = [("Fund Relief ($3.0B AUD)", pay, "#00843D")]
        if self.facilities["Flood-Catchment Plant"]["count"] > 0:
            options.append(("Release Rain Catchment Plan ($3.0B AUD)", rain_catchment, "#002B49"))
        options.append(("Ignore Crisis", ignore, "#CCCCCC"))

        self.show_overlay(
            "⚠️ CATASTROPHIC BUSHFIRES",
            "Intense summer heat has triggered massive bushfires. The nation demands emergency relief funds.",
            "#D9381E",
            options
        )

    def trigger_oil_spill(self):
        def clean_spill():
            self.debt += 2.0
            self.event_inflation_mod += 1.0
            self.senate_popularity = min(100.0, self.senate_popularity + 5.0)

        def modernise_plants():
            self.debt += 15.0
            self.oil_spill_prevented = True
            self.senate_popularity = min(100.0, self.senate_popularity + 10.0)

        def ignore_spill():
            self.event_happy_mod -= 10.0
            self.senate_popularity = max(0.0, self.senate_popularity - 10.0)

        self.show_overlay(
            "MASSIVE OIL SPILL",
            "One of your numerous Offshore Oil Rigs has ruptured! Environmental groups are furious.",
            "#000000",
            [
                ("Fund Cleanup ($2.0B AUD)", clean_spill, "#00843D"),
                ("Modernise Plants ($15.0B) - Prevent Forever", modernise_plants, "#002B49"),
                ("Ignore the Environment", ignore_spill, "#D9381E")
            ]
        )

    def trigger_fuel_crisis(self):
        def fund_relief():
            self.debt += 10.0
            self.event_inflation_mod += 5.0

        def ignore():
            self.event_happy_mod -= 20.0
            self.event_inflation_mod += 8.0

        self.show_overlay(
            "GLOBAL FUEL CRISIS",
            "The US and Indonesia did something dumb and blocked the Strait of Hormuz! Oil prices are skyrocketing. Do you deploy a massive $10B fuel relief package? It will raise inflation significantly.",
            "#8B0000",
            [
                ("Pass Relief Package ($10B AUD)", fund_relief, "#00843D"),
                ("Let the Market Decide", ignore, "#D9381E")
            ]
        )

    def trigger_bondi_event(self):
        self.bondi_event_occurred = True
        def resolve_speech(): self.event_happy_mod += 10; self.senate_popularity = min(100.0, self.senate_popularity + 2)
        def resolve_guns(): self.event_crime_mod -= 15; self.event_happy_mod += 5
        def resolve_crime(): self.event_crime_mod -= 10; self.immigration_policy.set("Moderate (35k/mo)"); self.senate_popularity = min(100.0, self.senate_popularity + 5)
        def resolve_ignore(): self.event_happy_mod -= 25; self.event_crime_mod += 10; self.senate_popularity = max(0.0, self.senate_popularity - 15)

        self.show_overlay(
            "TERROR ATTACK IN BONDI",
            "A tragic incident has occurred. The nation is in shock. As Prime Minister, how do you respond?",
            "#000000",
            [
                ("1. Deliver Strong Attack Speech", resolve_speech, "#333333"),
                ("2. Crack Down on Gun Laws", resolve_guns, "#333333"),
                ("3. Address Crime & Cut Immigration", resolve_crime, "#333333"),
                ("4. Ignore + Fake Apology", resolve_ignore, "#D9381E")
            ]
        )

    def trigger_recession(self):
        def exp():
            self.debt += 100.0
            infl_rise = 8.0
            self.event_inflation_mod += infl_rise
            self.recession_active = False
            self.recession_recovery_timer = 3
            self.senate_popularity = min(100.0, self.senate_popularity + 8.0)

            # Apply immediate standard inflation penalty to happiness based on the rise
            if (self.inflation + infl_rise) > 3.0:
                self.event_happy_mod -= (infl_rise * 3.5)

        def rel():
            self.debt += 5.0
            self.event_inflation_mod += 1.0
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def ign():
            self.event_happy_mod -= 15.0
            self.event_crime_mod += 10.0
            self.senate_popularity = max(0.0, self.senate_popularity - 15.0)

        self.show_overlay("ECONOMIC RECESSION", "The economy has entered a severe recession. Deflation and high unemployment are destroying livelihoods. It will cut revenue by $10B/mo and raise unemployment by 10%.", "#8B0000",
            [("Bailout Economy to fix crisis ($100.0B)", exp, "#00843D"),
             ("Targeted Stimulus ($5.0B)", rel, "#002B49"),
             ("Austerity (Ignore)", ign, "#CCCCCC")])

    def trigger_pandemic(self):
        def exp():
            self.debt += 20.0; self.event_happy_mod += 2.0; self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
        def rel():
            self.debt += 5.0; self.event_inflation_mod += 2.0; self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
        def ign():
            self.event_happy_mod -= 15.0; self.event_health_mod -= 20.0; self.senate_popularity = max(0.0, self.senate_popularity - 10.0)
        self.show_overlay("GLOBAL PANDEMIC", "A highly contagious virus is spreading rapidly across the globe.", "#8B0000",
            [("National Lockdown & Subsidies ($20.0B - No Infl)", exp, "#00843D"),
             ("Cheaper Relief Efforts ($5.0B - Infl +2%)", rel, "#002B49"),
             ("Ignore Crisis Entirely", ign, "#CCCCCC")])

    def trigger_market_crash(self):
        def exp():
            self.debt += 12.0; self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
        def rel():
            self.debt += 4.0; self.event_inflation_mod += 1.5; self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
        def ign():
            self.event_happy_mod -= 10.0; self.event_crime_mod += 5.0; self.senate_popularity = max(0.0, self.senate_popularity - 10.0)
        self.show_overlay("FINANCIAL MARKET CRASH", "Global markets are tumbling, threatening domestic jobs and retirement savings.", "#8B0000",
            [("Bailout & Absorb Damage ($12.0B - No Infl)", exp, "#00843D"),
             ("Distribute Stimulus Checks ($4.0B - Infl +1.5%)", rel, "#002B49"),
             ("Let It Bleed (Ignore)", ign, "#CCCCCC")])

    def trigger_supply_collapse(self):
        def exp():
            self.debt += 8.0; self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
        def rel():
            self.debt += 2.0; self.event_inflation_mod += 1.0; self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
        def ign():
            self.event_inflation_mod += 3.0; self.event_happy_mod -= 5.0; self.senate_popularity = max(0.0, self.senate_popularity - 8.0)
        self.show_overlay("SUPPLY CHAIN COLLAPSE", "Major global shipping routes are blocked. Imports are completely stalled.", "#8B0000",
            [("Subsidise Rapid Freight ($8.0B - No Infl)", exp, "#00843D"),
             ("Partial Subsidy Packages ($2.0B - Infl +1%)", rel, "#002B49"),
             ("Ignore Scarcity", ign, "#CCCCCC")])

    def trigger_grid_failure(self):
        def exp():
            self.debt += 10.0; self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
        def rel():
            self.debt += 3.0; self.event_inflation_mod += 0.5; self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
        def ign():
            self.event_happy_mod -= 12.0; self.event_crime_mod += 5.0; self.senate_popularity = max(0.0, self.senate_popularity - 10.0)
        self.show_overlay("NATIONAL GRID FAILURE", "A massive cascading failure has suddenly blacked out half the country.", "#000000",
            [("Rapid Subsidised Rebuild ($10.0B - No Infl)", exp, "#00843D"),
             ("Rolling Blackout Relief ($3.0B - Infl +0.5%)", rel, "#002B49"),
             ("Ignore (Blame Utilities)", ign, "#CCCCCC")])

    def trigger_debt_downgrade(self):
        def exp():
            self.debt += 15.0; self.senate_popularity = min(100.0, self.senate_popularity + 5.0)
        def rel():
            self.debt += 2.0; self.event_inflation_mod += 1.0; self.senate_popularity = min(100.0, self.senate_popularity + 2.0)
        def ign():
            self.event_inflation_mod += 2.0; self.debt += 10.0; self.senate_popularity = max(0.0, self.senate_popularity - 10.0)
        self.show_overlay("SOVEREIGN DEBT THREAT", "Credit agencies are actively threatening to aggressively downgrade our national rating.", "#8B0000",
            [("Immediate Foreign Repayment ($15.0B - No Infl)", exp, "#00843D"),
             ("Negotiate Stalled Terms ($2.0B - Infl +1%)", rel, "#002B49"),
             ("Ignore Threat", ign, "#CCCCCC")])

    def trigger_ram_shortage(self):
        def invest():
            self.debt += 15.0
            self.facilities["RAM Production Plant"]["count"] += 5
            if self.resource_levies["RAM (Req. Plant)"].get() < 10.0:
                self.foreign_relations = min(100.0, self.foreign_relations + 15.0)

        def relief():
            self.debt += 2.5
            self.event_inflation_mod += 2.5

        def ignore():
            self.event_happy_mod -= 5.0
            self.event_inflation_mod += 1.0

        self.show_overlay("⚠️ RAM SHORTAGE",
            "AI companies are buying too much RAM and its caused video games, electronics and computers to skyrocket in prices.",
            "#D9381E",
            [
                ("Domestic Production Investment ($15.0B AUD)", invest, "#00843D"),
                ("Financial Relief ($2.5B AUD, Infl +2.5%)", relief, "#002B49"),
                ("Ignore", ignore, "#CCCCCC")
            ]
        )

    def trigger_standard_event(self, event):
        def pay():
            self.debt += event["cost"]
            self.event_inflation_mod += (event["cost"] * 0.5)
            self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

        def ignore():
            if "happy" in event["penalties"]: self.event_happy_mod += event["penalties"]["happy"]
            if "health" in event["penalties"]: self.event_health_mod += event["penalties"]["health"]
            if "crime" in event["penalties"]: self.event_crime_mod += event["penalties"]["crime"]
            self.senate_popularity = max(0.0, self.senate_popularity - 5.0)

        self.show_overlay(
            "⚠️ " + event["name"].upper(),
            event["desc"],
            "#D9381E",
            [
                (f"Fund Relief (${event['cost']}B AUD)", pay, "#00843D"),
                ("Ignore Crisis", ignore, "#CCCCCC")
            ]
        )

    def advance_month(self):
        if self.in_election or self.in_event: return

        if getattr(self, 'recession_recovery_timer', 0) > 0:
            self.recession_recovery_timer -= 1
            if self.recession_recovery_timer == 0:
                messagebox.showinfo("Bailout Ended", "The $100B Fund Employment program has ended. Unemployment and Happiness are now fluctuating normally again.")

        if getattr(self, 'black_market_police_timer', 0) > 0:
            self.black_market_police_timer -= 1
            if self.black_market_police_timer == 0:
                self.event_crime_mod -= 15.0
                self.event_happy_mod += 5.0
                messagebox.showinfo("Black Market Crushed", "The $1.5B Police Package has successfully wiped out the black market operations!")

        if getattr(self, 'shale_boom_timer', 0) > 0:
            self.shale_boom_timer -= 1
            if self.shale_boom_timer == 0:
                self.shale_oil_penalty = 0.0
                messagebox.showinfo("Shale Oil Boom Ended", "The massive shale oil boom has stabilized, and market impacts have faded.")

        self.road_package_used_this_month = False

        # Record History before calculation shifts
        self.last_month_stats = {
            "inflation": self.inflation,
            "unemployment": self.unemployment,
            "happiness": self.happiness
        }

        self.last_month_policies = {
            "health": self.health_spend.get(),
            "education": self.education_spend.get(),
            "defence": self.defence_spend.get(),
            "police": self.police_spend.get(),
            "infra": self.infra_spend.get(),
            "pension": self.age_pension.get(),
            "jobseeker": self.jobseeker.get(),
            "gst": self.gst_rate.get(),
            "company_tax": self.company_tax_rate.get(),
            "income_tax_15": self.tax_bracket_15.get(),
            "sin_tax": self.sin_tax.get(),
            "fuel_excise": self.fuel_excise_rate.get()
        }

        self.term_happiness_history.append(self.happiness)
        self.term_crime_history.append(self.crime_index)
        if self.happiness > 75.0:
            self.months_happy_over_75 += 1

        if self.immigration_policy.get() == "Closed Borders (0/mo)":
            self.immigration_zero_months += 1
        else:
            self.immigration_zero_months = 0
            self.bigot_event_occurred = False

        if self.laws["Anti-Corruption & Lobbying Act"]["passed"]:
            if not hasattr(self, 'assassination_timer'):
                self.assassination_timer = random.randint(1, 10)
            self.assassination_timer -= 1
            if self.assassination_timer <= 0:
                self.show_overlay("ASSASSINATED", "You’ve pissed them off....", "#8B0000", [("Quit", lambda: self.return_to_main_menu(), "#000000")])
                return

        if self.satanism_assassination_timer > 0:
            self.satanism_assassination_timer -= 1
            if self.satanism_assassination_timer <= 0:
                self.show_overlay("ASSASSINATED", "You pissed them off.....", "#8B0000", [("Quit", lambda: self.return_to_main_menu(), "#000000")])
                return

        # Advance Lock Timers
        expired_locks = []
        for setting_key, lock in self.locked_settings.items():
            lock["months"] -= 1
            if lock["months"] <= 0:
                expired_locks.append(setting_key)
        for k in expired_locks:
            del self.locked_settings[k]

        # Advance Active Procurement Timers
        for proc in self.active_procurements[:]:
            proc["months_left"] -= 1
            if proc["months_left"] <= 0:
                self.active_procurements.remove(proc)

        self.month += 1
        self.term_month += 1
        self.total_months_played += 1

        if self.month > 12:
            self.month = 1
            self.year += 1

        if self.term_month == 1:
            self.events_this_term = 0
            self.term_happiness_history.clear()
            self.term_crime_history.clear()
            self.months_happy_over_75 = 0
            self.player_declared_wars_this_term = 0
            if self.total_months_played > 12:
                self.max_events_this_term = random.randint(1, 2)
            else:
                self.max_events_this_term = 0
        if self.total_months_played == 13:
            self.max_events_this_term = random.randint(1, 2)

        self.debt -= self.monthly_balance

        immig_num = {"Closed Borders (0/mo)": 0, "Low (15k/mo)": 15000, "Moderate (35k/mo)": 35000,
                     "High (75k/mo)": 75000, "Massive Open (150k/mo)": 150000}[self.immigration_policy.get()]

        self.population += immig_num + 8000

        if self.tariffs_timer > 0:
            self.tariffs_timer -= 1
            if self.tariffs_timer == 0:
                self.tariffs_boost_active = True
                messagebox.showinfo("Tariffs Lifted", "The 3 month broad tariffs have expired. Inflation has normalized and domestic production has boosted happiness by 2%!")

        completed_facilities = []
        for build in self.build_queue[:]:
            build["months_left"] -= 1
            if build["months_left"] <= 0:
                fac_name = build["name"]
                self.facilities[fac_name]["count"] += 1

                if fac_name in ["Nuclear Power Plant", "Coal Power Plant"]:
                    self.senate_popularity = min(100.0, self.senate_popularity + 2.0)

                if build.get("target"):
                    self.facility_protections[build["target"]][fac_name] += 1

                completed_facilities.append(fac_name)
                self.build_queue.remove(build)

        if completed_facilities:
            msg = "The following infrastructure projects are complete and fully operational:\n\n" + "\n".join(completed_facilities)
            messagebox.showinfo("Construction Complete!", msg)

        self.lbl_date.config(text=f"Term Month {self.term_month} / 36\n({self.year})")

        if self.is_at_war:
            self.war_duration -= 1

            if self.war_duration == 1 and not getattr(self, 'ground_invasion_done', False):
                if self.facilities["Abrams Tank package(x15)"]["count"] > 0 and self.facilities["Bushmaster package (x30)"]["count"] > 0:
                    st.session_state["confirmation"] = {
                        "title": "Ground Invasion Opportunity",
                        "message": f"The war is almost over! Begin ground invasion to annex {self.war_opponent}?\n\nCost: $3.0B AUD.",
                        "action": "late_ground_invasion",
                    }
                    return

            if self.war_duration <= 0:
                self.resolve_war()
                return

            if self.war_opponent == "China" and "Solomon Islands" not in self.defeated_countries:
                self.extra_war_event_pending = True
            else:
                self.extra_war_event_pending = False

            self.trigger_war_event_director()
            self.update_war_ui()
            return
        else:
            mil_score = self.calculate_military_score()
            if mil_score < 7.0 and random.random() < 0.05:
                self.trigger_invasion("China", 3)
                return

        if not self.check_random_events():
            self.recalculate_economy()
            self.generate_news()
            self.update_facilities_table()
            if self.term_month >= 36:
                self.trigger_election_debate()

    def calculate_power_mix(self):
        # 2025 Australian generation mix, used as the realistic starting point for the game.
        # New player-built capacity then shifts the mix progressively rather than replacing it instantly.
        baseline = {
            "Coal": 42.7,
            "Gas": 16.2,
            "Nuclear": 0.0,
            "Renewables": 34.8,
            "Hydro": 4.7,
            "Other": 1.7,
        }

        added = {key: 0.0 for key in baseline}
        added["Coal"] += self.facilities["Coal Power Plant"]["count"] * 1.00
        added["Gas"] += self.facilities["Open-Cycle Gas Plant"]["count"] * 0.60
        added["Gas"] += self.facilities["Combined Cycle Gas Plant"]["count"] * 1.00
        added["Nuclear"] += self.facilities["Nuclear Power Plant"]["count"] * 3.00
        added["Renewables"] += self.facilities["Solar Farm Grid"]["count"] * 0.45
        added["Renewables"] += self.facilities["Hydrogen Fuel Facility"]["count"] * 0.30
        added["Renewables"] += self.facilities["Geothermal Energy Plant"]["count"] * 0.30
        added["Hydro"] += self.facilities["Flood-Catchment Plant"]["count"] * 0.50

        totals = {key: baseline[key] + added[key] for key in baseline}
        total = sum(totals.values())
        return {key: (value / total) * 100.0 for key, value in totals.items()}

    def apply_power_mix_demand_effects(self, mix):
        # Power-source demand effects are deliberately modest so they complement, rather than replace,
        # the existing market drivers and price/demand feedback.
        hydrogen_count = self.facilities["Hydrogen Fuel Facility"]["count"]
        solar_count = self.facilities["Solar Farm Grid"]["count"]
        effects = {
            "Coal": 0.22 * (mix["Coal"] / 42.7),
            "LNG": 0.22 * (mix["Gas"] / 16.2),
            "Lithium": 0.18 * (mix["Renewables"] / 34.8) * max(1.0, solar_count / max(1.0, solar_count + hydrogen_count)),
            "Uranium": 0.30 * (mix["Nuclear"] / 5.0) if mix["Nuclear"] > 0 else 0.0,
            "Electricity": 0.20 * (sum(mix.values()) / 100.0) + (hydrogen_count * 0.035),
            "Water": 0.08 * (mix["Hydro"] / 4.7) + (hydrogen_count * 0.045),
        }
        for comm, strength in effects.items():
            if comm not in self.market_prices:
                continue
            data = self.market_prices[comm]
            base_demand = data.get("base_demand", 100.0)
            current_demand = data.get("demand", base_demand)
            multiplier = max(0.70, min(1.60, 1.0 + strength))
            data["demand"] = min(100.0, current_demand * multiplier)

            # Only a small fraction of the demand change feeds back into price.
            current_price = max(float(data.get("current", data["base"])), 0.000001)
            data["current"] = current_price * (1.0 + min(0.035, max(-0.02, (multiplier - 1.0) * 0.035)))

    def get_gfp_ranking(self):
        # 2026 Global Firepower top-15 reference ranking. Lower PwrIndx is stronger.
        reference = [
            ("United States", 0.0741), ("Russia", 0.0791), ("China", 0.0919),
            ("India", 0.1346), ("South Korea", 0.1642), ("France", 0.1798),
            ("Japan", 0.1876), ("United Kingdom", 0.1881), ("Turkiye", 0.1975),
            ("Italy", 0.2211), ("Brazil", 0.2374), ("Germany", 0.2463),
            ("Indonesia", 0.2582), ("Pakistan", 0.2626), ("Indonesia", 0.2707),
        ]

        # GFP is deliberately slower than the raw military-score system and uses a broader set of assets.
        warships = (self.facilities["Hobart Class Destroyer"]["count"] +
                    self.facilities["Hunter Class Frigate"]["count"] +
                    self.facilities["Mongami Frigate"]["count"])
        nuclear_submarines = self.facilities["Nuclear Submarine (x3)"]["count"] * 3
        abrams_tanks = self.facilities["Abrams Tank package(x15)"]["count"] * 15
        bushmasters = self.facilities["Bushmaster package (x30)"]["count"] * 30
        fighter_assemblies = self.facilities["Advanced Fighter Jet Assembly"]["count"]
        weapon_plants = self.facilities["Weapon Manufacturing Plant"]["count"]
        airbases = self.facilities["Upgraded Airbase"]["count"]
        fighter_squadrons = self.facilities["F-15 Fighter Squadron"]["count"]
        bomber_squadrons = self.facilities["B-52H Bomber Squadron Fleet"]["count"]
        cyber = self.facilities["Cyber Security Division"]["count"]
        satellite = self.facilities["Satellite Grid"]["count"]
        navy_bases = self.facilities["Naval Submarine Base"]["count"]
        nuke_plants = self.facilities["Nuclear Power Plant"]["count"]
        defence = self.defence_spend.get()

        force_strength = (
            0.25 * (self.population / 1_000_000.0) +
            1.20 * defence +
            0.70 * warships +
            1.20 * nuclear_submarines +
            0.45 * abrams_tanks +
            0.25 * bushmasters +
            2.00 * fighter_assemblies +
            0.75 * weapon_plants +
            1.00 * airbases +
            1.50 * fighter_squadrons +
            2.20 * bomber_squadrons +
            3.00 * cyber +
            2.50 * satellite +
            1.75 * navy_bases +
            3.50 * nuke_plants +
            12.0 * self.facilities["Ballistic Missile Program"]["count"] +
            18.0 * self.facilities["Nuclear Program"]["count"]
        )
        baseline_strength = getattr(self, "_gfp_initial_strength", None)
        if baseline_strength is None:
            baseline_strength = force_strength
            self._gfp_initial_strength = baseline_strength

        australia_score = 0.3208 * math.exp(-0.0075 * max(0.0, force_strength - baseline_strength))
        australia_score = max(0.045, min(0.65, australia_score))

        # Hard GFP gates: a conventional buildup cannot leap into the very top ranks prematurely.
        top8_ready = (
            warships >= 15 and cyber >= 1 and satellite >= 1 and nuke_plants >= 2 and
            defence >= 6.0 and weapon_plants >= 6 and fighter_squadrons >= 3 and
            bomber_squadrons >= 2 and airbases >= 6
        )
        top4_ready = (
            self.facilities["Nuclear Program"]["count"] >= 1 and
            self.facilities["Ballistic Missile Program"]["count"] >= 1 and
            nuclear_submarines >= 6 and abrams_tanks >= 150 and bushmasters >= 300 and
            fighter_assemblies >= 5 and weapon_plants >= 15 and navy_bases >= 3 and
            nuke_plants >= 5 and defence >= 20.0 and
            self.immigration_policy.get() == "Closed Borders (0/mo)" and cyber >= 1 and satellite >= 1
        )

        if not top4_ready:
            australia_score = max(australia_score, reference[3][1] + 0.0002)
        if not top8_ready:
            australia_score = max(australia_score, reference[8][1] + 0.0002)

        ranking = reference + [("Australia", australia_score)]
        ranking.sort(key=lambda item: item[1])
        return ranking[:15], australia_score

    def setup_news_tab(self):
        container = tk.Frame(self.tab_news, bg="#F4F6F9")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        lbl = tk.Label(container, text="📰 Monthly News Network", bg="#F4F6F9", fg="black", font=("Helvetica", 14, "bold"))
        lbl.pack(anchor="w", pady=(0, 10))

        v_scroll = ttk.Scrollbar(container, orient="vertical")
        v_scroll.pack(side="right", fill="y")

        h_scroll = ttk.Scrollbar(container, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        self.news_text = tk.Text(container, wrap="none", font=("Helvetica", 12), bg="white", fg="black",
                                 yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set,
                                 height=20, width=80)
        self.news_text.pack(side="left", fill="both", expand=True)

        v_scroll.config(command=self.news_text.yview)
        h_scroll.config(command=self.news_text.xview)

        self.news_text.insert(tk.END, "No news available yet. Advance a month to see updates.")
        self.news_text.config(state="disabled")

    def generate_news(self):
        if not hasattr(self, 'news_text'):
            return
        try:
            if not self.news_text.winfo_exists():
                return
        except tk.TclError:
            return

        self.news_text.config(state="normal")
        self.news_text.delete("1.0", tk.END)

        headlines = []
        old_infl = getattr(self, 'last_month_stats', {}).get("inflation", self.inflation)
        old_unemp = getattr(self, 'last_month_stats', {}).get("unemployment", self.unemployment)
        old_happ = getattr(self, 'last_month_stats', {}).get("happiness", self.happiness)

        # 1. Inflation & Economy Deltas
        if self.inflation > old_infl + 0.5:
            headlines.append(f"Inflation jumps to {self.inflation:.1f}%, hurting household savings and happiness.")
        elif self.inflation < old_infl - 0.5:
            headlines.append(f"Inflation drops to {self.inflation:.1f}%, increasing overall national happiness.")

        if self.unemployment > old_unemp + 0.5:
            headlines.append(f"Unemployment rises to {self.unemployment:.1f}%, severely lowering public morale.")
        elif self.unemployment < old_unemp - 0.5:
            headlines.append(f"Unemployment falls to {self.unemployment:.1f}%, drastically boosting public morale.")

        if self.happiness < 40.0:
            headlines.append(f"Public happiness at a dismal {self.happiness:.1f}%. Citizens demand government change.")
        elif self.happiness > 80.0:
            headlines.append(f"Happiness soars to {self.happiness:.1f}%. The government maintains incredibly strong support.")

        # 2. Taxes and Welfare
        old_pol = getattr(self, 'last_month_policies', {})
        if old_pol:
            if self.gst_rate.get() > old_pol.get("gst", 10.0):
                headlines.append("Public outrage grows as recent GST rate hikes squeeze household budgets.")
            elif self.gst_rate.get() < old_pol.get("gst", 10.0):
                headlines.append("Retailers and shoppers celebrate recent GST cuts, sparking a domestic spending boom.")

            if self.sin_tax.get() > old_pol.get("sin_tax", 65.0):
                headlines.append("Smokers and drinkers hit hard by aggressive new Sin Tax hikes, angering locals.")
            elif self.sin_tax.get() < old_pol.get("sin_tax", 65.0):
                headlines.append("Cheap alcohol and tobacco floods the market after Sin Tax drops; health experts worry.")

            if self.health_spend.get() > old_pol.get("health", 8.5):
                headlines.append("Healthcare sector praises government for massive Medicare funding boost.")
            elif self.health_spend.get() < old_pol.get("health", 8.5):
                headlines.append("Hospitals overwhelmed! Severe Medicare cuts leave emergency rooms completely strained.")

            if self.education_spend.get() > old_pol.get("education", 4.0):
                headlines.append("Education sector revitalized as federal funding flows into schools and universities.")
            elif self.education_spend.get() < old_pol.get("education", 4.0):
                headlines.append("Teachers unions warn of impending youth crime crisis due to severe education funding cuts.")

            if self.defence_spend.get() > old_pol.get("defence", 4.2):
                headlines.append("Military leaders applaud the Prime Minister's massive increase to the defence budget.")
            elif self.defence_spend.get() < old_pol.get("defence", 4.2):
                headlines.append("National security concerns arise as government slashes the defence budget.")

            if self.age_pension.get() < old_pol.get("pension", 1200.0):
                headlines.append("Elderly citizens protest outside parliament over devastating pension cuts.")
            elif self.age_pension.get() > old_pol.get("pension", 1200.0):
                headlines.append("Retirees rejoice as generous Age Pension increases provide immense cost-of-living relief.")

            if self.jobseeker.get() > old_pol.get("jobseeker", 1.2):
                headlines.append("Welfare advocates praise the recent boosts to JobSeeker payments.")
            elif self.jobseeker.get() < old_pol.get("jobseeker", 1.2):
                headlines.append("Unemployed citizens struggle to survive following harsh JobSeeker welfare cuts.")

        if self.annual_wealth_tax.get() > 0.0:
            headlines.append("Business leaders furiously criticize the new Annual Wealth Tax, warning of massive capital flight.")
        if self.wage_cpi_index.get() > 1.5:
            headlines.append("Mounting costs of doing business! News agencies heavily criticize extreme wage indexation.")

        # 3. Real Disasters and Events
        if hasattr(self, 'recent_news') and self.recent_news:
            for news_item in self.recent_news:
                headlines.append(news_item)
            self.recent_news.clear()

        # 4. Market and Commodities
        petrol_price = self.market_prices.get("Petrol", {}).get("current", 2.0)
        diesel_price = self.market_prices.get("Diesel", {}).get("current", 2.15)
        beef_price = self.market_prices.get("Beef", {}).get("current", 12.0)
        elec_price = self.market_prices.get("Electricity", {}).get("current", 25.0)

        if petrol_price > 2.5:
            headlines.append(f"Petrol skyrockets to ${petrol_price:.2f}/L! Commuters furious over transport costs.")
        elif petrol_price < 1.5:
            headlines.append(f"Petrol prices plummet to ${petrol_price:.2f}/L, providing massive relief for daily commuters!")

        if diesel_price < 1.8:
            headlines.append("Truckies and freight operators celebrate as diesel prices plummeted significantly under this government!")

        if beef_price > 13.0:
            headlines.append("Beef prices surge on the market, hitting Aussie BBQ traditions hard.")
        elif beef_price < 9.0:
            headlines.append("Cheaper beef prices lead to a massive surge in domestic meat consumption.")

        natural_resource_tariff = self.tariffs["Energy & Natural Resources"].get()
        agricultural_tariff = self.tariffs["Agricultural products"].get()
        if natural_resource_tariff >= 5.0 and random.random() < 0.35:
            headlines.append("Manufacturers and energy users criticize natural-resource tariffs after metals and fuel prices rise.")
        if agricultural_tariff >= 5.0 and random.random() < 0.35:
            headlines.append("Farmers, grocers and consumers criticize agricultural tariffs as food prices rise in the short term.")

        if self.laws.get("Interest Rate Cap Act", {}).get("passed") and random.random() < 0.25:
            headlines.append("Banks warn that the interest-rate cap could push lenders and loan capital offshore.")

        if elec_price < 15.0:
            headlines.append("Electricity prices drop dramatically as strong power infrastructure policies pay off!")
        elif elec_price > 35.0:
            headlines.append("Power bills soar! Citizens demand immediate action on the failing energy grid.")

        if self.market_prices.get("Crude Oil", {}).get("current", 80.0) >= 80.0 and self.resource_levies["Crude Oil"].get() < 5.0:
            headlines.append("Market prices are high for crude oil, levies should be placed for domestic supply and refining!")

        if self.facilities.get("RAM Production Plant", {}).get("count", 0) == 0:
            headlines.append("Ongoing RAM shortages cause video games and electronics prices to drastically skyrocket.")
        else:
            headlines.append("Domestic RAM production successfully stabilizes electronics and tech markets.")

        # 5. Wars, Events, and Military Updates
        if self.is_at_war:
            headlines.append(f"War with {self.war_opponent} heavily impacts the economy and drains public hope.")
        if getattr(self, 'nuclear_sanctions', False):
            headlines.append("Severe international nuclear sanctions continue to choke Australian export revenues.")
        if self.recession_active:
            headlines.append("NATION IN RECESSION: Markets tumble as economic growth completely stalls.")
        if self.unemployment_event_occurred:
            headlines.append("Massive unemployment crisis sweeps the nation as job centers overflow.")
        if getattr(self, 'bigot_event_occurred', False):
            headlines.append("Greens publicly slam PM over 'Bigoted' zero-immigration border closures.")

        if self.facilities["Nuclear Program"]["count"] > 0:
            headlines.append("Australia officially enters the nuclear age, drawing intense global scrutiny.")
        if self.facilities["Ballistic Missile Program"]["count"] > 0:
            headlines.append("New domestic ballistic missile program signals an aggressive shift in defense posture.")

        fillers = [
            "Government economic policies under heavy scrutiny as global indicators fluctuate.",
            "Debate over the federal budget completely dominates parliament this week.",
            "Citizens demand immediate action on housing and basic living expenses.",
            "Global trade shifts heavily affect domestic markets and national revenue.",
            "Environmental and industry policies clash in recent heated senate discussions."
        ]

        random.shuffle(headlines)
        random.shuffle(fillers)

        selected_headlines = headlines[:5]
        while len(selected_headlines) < 5 and fillers:
            selected_headlines.append(fillers.pop(0))

        publishers = ["ABC", "SBS", "The Australian", "Sky News", "9Now", "The Guardian", "Channel 7"]

        for hl in selected_headlines[:5]:
            pub = random.choice(publishers)
            self.news_text.insert(tk.END, f"[{pub}] {hl}\n\n")

        # POWER %
        power_mix = self.calculate_power_mix()
        self.news_text.insert(tk.END, "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        self.news_text.insert(tk.END, "POWER %\n")
        self.news_text.insert(tk.END, "Current estimated electricity generation mix\n\n")
        power_lines = [
            ("Coal", power_mix["Coal"]),
            ("Gas", power_mix["Gas"]),
            ("Nuclear", power_mix["Nuclear"]),
            ("Renewables (Solar / Hydrogen / Geothermal)", power_mix["Renewables"]),
            ("Hydropower (Flood-Catchment / Dams)", power_mix["Hydro"]),
            ("Other / Oil", power_mix["Other"]),
        ]
        for label, pct in power_lines:
            self.news_text.insert(tk.END, f"{label:<42} {pct:5.1f}%\n")

        self.news_text.insert(tk.END, "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        self.news_text.insert(tk.END, "GLOBAL FIREPOWER INDEX (GFP)\n")
        self.news_text.insert(tk.END, "Monthly conventional military-strength ranking\n\n")
        gfp_top15, australia_score = self.get_gfp_ranking()
        for idx, (country, score) in enumerate(gfp_top15, 1):
            marker = "  ← Australia" if country == "Australia" else ""
            self.news_text.insert(tk.END, f"{idx:>2}. {country:<20} PwrIndx {score:.4f}{marker}\n")
        if not any(country == "Australia" for country, _ in gfp_top15):
            self.news_text.insert(tk.END, f"\nAustralia: outside the top 15  |  PwrIndx {australia_score:.4f}\n")

        self.news_text.config(state="disabled")

    def trigger_election_debate(self):
        self.in_election = True
        avg_happ = sum(self.term_happiness_history) / len(self.term_happiness_history) if self.term_happiness_history else self.happiness
        avg_crime = sum(self.term_crime_history) / len(self.term_crime_history) if self.term_crime_history else self.crime_index
        st.session_state["election"] = {"avg_happ": avg_happ, "avg_crime": avg_crime}


# ==================== STREAMLIT PRESENTATION / INTERACTION LAYER ====================

def _init_game():
    if "game" not in st.session_state:
        st.session_state["game"] = AustraliaBudgetGame(_Root())
        st.session_state["game_started"] = False
        st.session_state["notifications"] = []
        st.session_state["overlay"] = None
        st.session_state["confirmation"] = None
        st.session_state["pending_build"] = None
        st.session_state["election"] = None
        st.session_state["party_selection"] = "Labour"


def _sync_vars(game):
    game.recalculate_economy()


def _complete_build(game):
    data = st.session_state.get("pending_build")
    if not data: return
    fac_name=data["name"]; cost=data["cost"]; build_time=data["build_time"]; target=data.get("target")
    if fac_name == "Nuclear Program":
        game.nuclear_sanctions=True; game.event_inflation_mod += 5.0; game.foreign_relations=0.0
        messagebox.showwarning("NUCLEAR SANCTIONS TRIGGERED", "The international community has heavily sanctioned Australia for pursuing a Nuclear Program!\n\nAll export levy profits have been shut down, inflation has spiked by 5%, and Foreign Relations have crashed to 0%.")
    game.debt += cost
    game.build_queue.append({"name":fac_name,"months_left":build_time,"target":target})
    game.active_procurements.append({"name":fac_name,"cost":cost,"months_left":build_time+6})
    messagebox.showinfo("Construction Started", f"Construction started on {fac_name}.\nIt will be fully operational in {build_time} months.")
    st.session_state["pending_build"]=None
    game.update_facilities_table(); game.recalculate_economy(); game.generate_news()


def _resolve_confirmation(game, answer):
    c=st.session_state.get("confirmation")
    if not c: return
    action=c["action"]
    st.session_state["confirmation"]=None
    if not answer:
        st.session_state["pending_build"]=None; st.session_state["pending_abolish"]=None; st.session_state["pending_war_declaration"]=None; st.session_state["pending_law_demand"]=None
        return
    if action == "confirm_build":
        data=st.session_state.get("pending_build")
        if data and data["name"] in ["Patriot Battery","THAAD System"]:
            targets=["Oil Refinery","LNG Processing Facility","Offshore Oil Rig","Coal Power Plant","Nuclear Power Plant","Advanced Fighter Jet Assembly","Naval Submarine Base","Pine Gap Intelligence Base","Zinc Refinery","Nickel Refinery","Tungsten Refinery"]
            valid=[t for t in targets if game.facilities[t]["count"]>0]
            valid.extend(game.airbase_names)
            built=[t for t in valid if (t in game.airbase_names and game.airbase_names.index(t)<game.facilities["Upgraded Airbase"]["count"]) or (t not in game.airbase_names and game.facilities[t]["count"]>0)]
            if not built:
                messagebox.showerror("No Valid Targets", f"You have no valid built infrastructure to protect with a {data['name']} yet!"); st.session_state["pending_build"]=None; return
            st.session_state["target_select"]={"options":built,"kind":"build"}
            return
        _complete_build(game)
    elif action == "confirm_abolish":
        data=st.session_state.get("pending_abolish")
        if data:
            fac_name=data["name"]; refund=data["refund"]; game.facilities[fac_name]["count"]-=1; game.debt-=refund
            if fac_name in ["Patriot Battery","THAAD System"]:
                for t in game.facility_protections:
                    if game.facility_protections[t][fac_name]>0: game.facility_protections[t][fac_name]-=1; break
            messagebox.showinfo("Facility Abolished", f"{fac_name} has been permanently dismantled.\n${refund:.2f}B AUD recovered.")
            st.session_state["pending_abolish"]=None; game.update_facilities_table(); game.recalculate_economy()
    elif action == "confirm_war":
        d=st.session_state.get("pending_war_declaration")
        if d:
            game.is_at_war=True; game.war_opponent=d["target"]; game.war_tier=d["tier"]; game.war_duration=random.randint(3,18); game.player_declared_wars_this_term+=1; game.ally_called_this_war=False; game.ground_invasion_done=False; game.update_war_ui(); game.recalculate_economy(); game.recent_news.append(f"BREAKING: Australia officially declares war on {game.war_opponent}!"); messagebox.showwarning("WAR DECLARED", f"Australia is now at war with {game.war_opponent}!\nExpected conflict duration: {game.war_duration} months."); st.session_state["pending_war_declaration"]=None
    elif action == "accept_law_demand":
        d=st.session_state.get("pending_law_demand")
        if d:
            law_name=d["law_name"]; demand=d["demand"]; demand["action"](); game.locked_settings[demand["setting_key"]]={"val":demand["get_val"](),"months":3,"party":demand["party"]}; game.laws[law_name]["passed"]=True; game.senate_popularity=min(100.0,game.senate_popularity+2.0)
            if not hasattr(game,"recent_news"): game.recent_news=[]
            if law_name == "Block Foreign Property Purchases": game.recent_news.append("Real estate market shakes as foreigners are officially banned from buying Australian homes.")
            elif law_name == "ADF Domestic Dispatch Act": game.recent_news.append("Military on the streets! ADF deployed domestically to combat rising crime waves.")
            elif law_name == "Illigalise Santanism": game.recent_news.append("Controversial new law outlaws Satanism nationwide, sparking severe underground protests.")
            elif law_name == "Universal Basic Income Trial": game.recent_news.append("Citizens celebrate as Universal Basic Income trial injects massive cash into local economies.")
            elif law_name == "Ban E-Cigarettes & Vapes": game.recent_news.append("Vape ban fully enforced! Health improves, but black market crime spikes significantly.")
            else: game.recent_news.append(f"New Legislation Passed: '{law_name}' becomes official federal law.")
            if law_name == "Illigalise Santanism":
                game.satanism_passed_count += 1
                if game.satanism_passed_count == 1: game.force_market_crash=True
                elif game.satanism_passed_count >= 2: game.satanism_assassination_timer=random.randint(2,6)
            if law_name == "Block Foreign Property Purchases":
                months=24 if game.immigration_policy.get()=="Closed Borders (0/mo)" else 12; game.housing_crisis_blocked_until=game.term_month+months
            messagebox.showinfo("Demand Accepted", f"{demand['party']} backed your bill! The demand was implemented, locked for 3 months, and the law passed."); st.session_state["pending_law_demand"]=None; game.recalculate_economy()
    elif action == "late_ground_invasion":
        game.debt+=3.0; game.ground_invasion_done=True; game.recent_news.append(f"Military Command: Australian troops launch late ground invasion of {game.war_opponent}.")
        if game.is_at_war:
            if game.war_opponent == "China" and "Solomon Islands" not in game.defeated_countries:
                game.extra_war_event_pending = True
            else:
                game.extra_war_event_pending = False
            game.trigger_war_event_director()
            game.update_war_ui()
    if st.session_state.get("overlay") is None and st.session_state.get("target_select") is None and st.session_state.get("confirmation") is None:
        game.recalculate_economy(); game.generate_news()


def _resolve_overlay(game, index):
    ov=st.session_state.get("overlay")
    if not ov: return
    buttons=ov["buttons"]
    if index >= len(buttons): return
    cmd=buttons[index][1]
    st.session_state["overlay"]=None; game.in_event=False
    cmd()
    if st.session_state.get("overlay") is None and st.session_state.get("confirmation") is None and not game.in_event:
        game.recalculate_economy(); game.generate_news()
        if game.term_month >= 36 and not game.in_election: game.trigger_election_debate()


def render_party_screen(game):
    st.markdown('<div class="hero">WELCOME, PRIME MINISTER<div class="subtitle">AUSTRALIAN FEDERAL COMMAND</div></div>', unsafe_allow_html=True)
    st.write("Pick your political party to begin:")
    party=st.radio("Political Party", ["Labour","Greens","Liberal","One Nation","Nationals"], index=["Labour","Greens","Liberal","One Nation","Nationals"].index(st.session_state.get("party_selection","Labour")), horizontal=False, label_visibility="collapsed")
    st.session_state["party_selection"]=party
    if st.button("START GAME", type="primary", use_container_width=True):
        game.ruling_party=party; game.in_event=False
        if party in ["Liberal","Nationals","One Nation"]:
            game.recent_news.append(f"[Sky News] Markets rally and citizens rejoice as {party} wins the election!"); game.recent_news.append(f"[The Guardian] Dark day for climate and progressive policies as {party} takes power.")
        else:
            game.recent_news.append(f"[Sky News] Economic fears rise as left-wing {party} claims election victory!"); game.recent_news.append(f"[The Guardian] A progressive leap forward! {party} forms new government.")
        game.generate_news(); st.session_state["game_started"]=True; st.rerun()


def render_overlay(game):
    ov=st.session_state.get("overlay")
    if not ov: return
    st.markdown(f'<div class="overlay"><h2>{ov["title"]}</h2><p>{ov["desc"].replace(chr(10),"<br>")}</p></div>', unsafe_allow_html=True)
    for i,(text,cmd,bg) in enumerate(ov["buttons"]):
        if st.button(text, key=f"ov_{i}_{abs(hash(text))}", use_container_width=True): _resolve_overlay(game,i); st.rerun()


def render_confirmation(game):
    c=st.session_state.get("confirmation")
    if not c: return
    st.markdown(f'<div class="overlay"><h2>{c["title"]}</h2><p>{c["message"].replace(chr(10),"<br>")}</p></div>', unsafe_allow_html=True)
    a,b=st.columns(2)
    if a.button("YES / CONFIRM", type="primary", use_container_width=True): _resolve_confirmation(game,True); st.rerun()
    if b.button("NO / CANCEL", use_container_width=True): _resolve_confirmation(game,False); st.rerun()


def render_target_select(game):
    d=st.session_state.get("target_select")
    if not d: return
    st.markdown('<div class="overlay"><h2>Assign Defence Target</h2><p>Select the infrastructure this system will exclusively protect.</p></div>', unsafe_allow_html=True)
    target=st.selectbox("Defence Target", d["options"], key="def_target")
    a,b=st.columns(2)
    if a.button("ASSIGN TARGET", type="primary", use_container_width=True):
        game.build_queue
        st.session_state["pending_build"]["target"]=target; st.session_state["target_select"]=None; _complete_build(game); st.rerun()
    if b.button("CANCEL", use_container_width=True): st.session_state["target_select"]=None; st.session_state["pending_build"]=None; st.rerun()


def render_header(game):
    st.markdown('<div class="topbar"><b>AUSTRALIAN FEDERAL COMMAND</b></div>', unsafe_allow_html=True)
    cols=st.columns(7)
    vals=[("Monthly Balance",f"${game.monthly_balance:.2f}B AUD"),("National Debt",f"${game.debt:.1f}B AUD"),("Average Interest Rate",f"{game.avg_interest_rate:.1f}%"),("Happiness",f"{game.happiness:.1f}%"),("Unemployment",f"{game.unemployment:.1f}%"),("Inflation",f"{game.inflation:.1f}%"),("Term Progress",f"Term Month {game.term_month} / 36\n({game.year})")]
    for c,(t,v) in zip(cols,vals): c.metric(t,v)
    cols2=st.columns(3)
    cols2[0].progress(min(1.0,max(0.0,game.power_bills/300.0)), text=f"Avg. Power Bills: ${game.power_bills:.0f}/mo AUD")
    cols2[1].progress(min(1.0,max(0.0,game.foreign_relations/100.0)), text=f"Foreign Relations: {game.foreign_relations:.1f}%")
    cols2[2].progress(min(1.0,max(0.0,game.crime_index/100.0)), text=f"Crime Index: {game.crime_index:.1f}/100")


def slider_set(label,var,min_v,max_v,fmt=None,step=None):
    if step is None: step=(max_v-min_v)/200.0
    val=st.slider(label, min_value=float(min_v), max_value=float(max_v), value=float(var.get()), step=float(step), key=f"slider_{label}")
    var.set(val)
    return val


def render_budget(game):
    a,b,c=st.columns(3)
    with a:
        st.subheader("MAIN FUNDING ($B / Month)")
        for lab,var,lo,hi in [("Health & Medicare:",game.health_spend,0,30),("Education & Universities:",game.education_spend,0,20),("Housing Subsidies:",game.housing_spend,0,20),("Police & National Security:",game.police_spend,0,15),("Defence Forces:",game.defence_spend,0,20),("Public Infrastructure:",game.infra_spend,0,18),("Foreign Aid:",game.foreign_aid,0,10),("Arts & Culture:",game.arts_funding,0,5),("Environment Protection:",game.env_spend,0,8),("Climate Change Funding:",game.climate_spend,0,13),("Net Zero Funding:",game.net_zero_spend,0,12)]: slider_set(lab,var,lo,hi)
    with b:
        st.subheader("WELFARE ($ AUD / Month)")
        slider_set("Age Pension:",game.age_pension,0,3000,step=10); slider_set("Aged Care Coverage:",game.aged_care_cover,0,100,step=1); slider_set("NDIS (Disability Support):",game.ndis_spend,0,60); slider_set("JobSeeker / Dole:",game.jobseeker,0,15); slider_set("Family Tax Benefits:",game.family_benefits,0,1000,step=10)
    with c:
        st.subheader("TAXATION (%)")
        for lab,var,lo,hi,step in [("Inc. Tax ($18k-$45k):",game.tax_bracket_15,0,40,0.5),("Inc. Tax ($45k-$135k):",game.tax_bracket_30,0,50,0.5),("Inc. Tax ($134k-$190k):",game.tax_bracket_37,0,60,0.5),("Inc. Tax ($190k+):",game.tax_bracket_45,0,70,0.5),("Company Tax Rate:",game.company_tax_rate,0,40,0.5),("Small Business Tax:",game.small_business_tax,0,40,0.5),("Payroll Tax:",game.payroll_tax,0,15,0.5),("GST Rate:",game.gst_rate,0,25,0.5),("Super Tax Rate:",game.super_tax_rate,0,35,0.5),("Fuel Excise:",game.fuel_excise_rate,0,100,0.5),("Land Tax Rate:",game.land_tax,0,10,0.1),("Sin Tax (Alcohol/Tobacco):",game.sin_tax,0,150,1),("Negative Gearing (100=Full):",game.negative_gearing,0,100,1),("Capital Gains Discount:",game.cgt_discount,0,100,1),("Fringe Benefits Tax:",game.fbt_rate,0,100,1),("Medicare Levy:",game.medicare_levy,0,5,0.1),("Infrastructure Levy:",game.infrastructure_levy,0,5,0.1),("Luxury Car Tax:",game.luxury_car_tax,0,100,1),("Annual Wealth Tax:",game.annual_wealth_tax,0,10,0.1),("Financial Trans. Tax:",game.fin_trans_tax,0,5,0.1),("Wages vs CPI Index:",game.wage_cpi_index,-2.5,2.5,0.1)]: slider_set(lab,var,lo,hi,step=step)
    game.recalculate_economy()


def render_facilities(game):
    game.update_facilities_table(); rows=[]
    for name,data in game.facilities.items():
        if name=="Pine Gap Intelligence Base": continue
        building=sum(1 for b in game.build_queue if b["name"]==name)
        rows.append({"Facility Name":name,"Sector Type":data["type"],"Active Count":f"{data['count']}"+(f" (+{building} Building)" if building else ""),"Build Cost ($B AUD)":f"${data['cost']}","Upkeep ($B AUD/mo)":f"${data['upkeep']}","Revenue ($B AUD/mo)":f"${data['rev']}","Workers Needed":f"{data['workers']:,}"})
    st.dataframe(rows,use_container_width=True,hide_index=True)
    names=[r["Facility Name"] for r in rows]; selected=st.selectbox("Facility",names,key="facility_selected")
    i=next(i for i,r in enumerate(rows) if r["Facility Name"]==selected); game.fac_tree._selection=[i]; game.fac_tree.rows=[tuple(rows[j].values()) for j in range(len(rows))]
    c1,c2,c3=st.columns(3)
    if c1.button("BUILD SELECTED FACILITY",use_container_width=True): game.build_facility(); st.rerun()
    if c2.button("ABOLISH SELECTED FACILITY",use_container_width=True): game.abolish_facility(); st.rerun()
    if c3.button("FUND $2B ROAD PACKAGE",use_container_width=True): game.enact_road_package(); st.rerun()


def render_war(game):
    st.subheader("Global Conflict & Military Command")
    st.write("Status:", f"AT WAR with {game.war_opponent} ({game.war_duration} months remaining)" if game.is_at_war else "PEACE")
    targets=[("Low Power Status Nations",1,["PNG","Fiji","New Zealand","Solomon Islands"]),("Medium Power Status Nations",2,["Philippines","Japan","Taiwan","Indonesia"]),("Large Power Status Nations",3,["United States","Russia","China","India"])]
    for cat,tier,nations in targets:
        st.markdown(f"**{cat}**")
        cols=st.columns(4)
        for col,n in zip(cols,nations):
            disabled=n in game.defeated_countries
            if col.button(f"Declare War on {n}",key=f"war_{n}",disabled=disabled,use_container_width=True): game.declare_war(n,tier); st.rerun()
    attacks=[("Air Strike ($1.0B)",1.0,game.req_air_strike,"Requires F-15 or B-52H AND Air-Surface Munitions.","Air Strike"),("Missile Barrage ($2.0B)",2.0,game.req_missile_barrage,"Requires Air-Surface or Naval Munitions.","Missile Barrage"),("Drone Barrage ($100M)",0.1,game.req_drone_barrage,"Requires Drone Manufacturing Plant.","Drone Barrage"),("Cyber Attack ($100M)",0.1,game.req_cyber_attack,"Requires Cyber Security Division.","Cyber Attack"),("Naval Strike ($2.0B)",2.0,game.req_naval_strike,"Requires a Warship (Hobart/Hunter/Mongami) AND Naval Munitions.","Naval Strike"),("Submarine Strike ($2.0B)",2.0,game.req_submarine_strike,"Requires Submarine/Naval Base AND Naval Munitions.","Submarine Strike"),("Conventional Ballistic Strike ($5.0B)",5.0,game.req_ballistic_strike,"Requires Ballistic Missile Program.","Conventional Ballistic Strike"),("Nuclear Sub Strike ($50.0B)",50.0,game.req_nuke_sub_strike,"Requires Nuclear Submarine AND Nuclear Program.","Nuclear Sub Strike"),("Nuclear Strike ($100.0B)",100.0,game.req_nuclear_strike,"Requires Nuclear Program.","Nuclear Strike"),("Ground Invasion ($3.0B)",3.0,game.req_ground_invasion,"Requires Abrams Tank AND Bushmaster.","Ground Invasion")]
    st.markdown("**Active War Commands & Strikes**")
    cols=st.columns(4)
    for i,(txt,cost,rf,msg,name) in enumerate(attacks):
        if cols[i%4].button(txt,key=f"atk_{i}",use_container_width=True): game.execute_player_attack(name,cost,rf,msg); st.rerun()


def render_laws_tab(game):
    st.subheader(f"Estimated Senate Popularity: {game.senate_popularity:.1f}%")
    if st.button("Fund Employment Programs ($10.0B AUD)",use_container_width=True): game.fund_employment(); st.rerun()
    for name,info in game.laws.items():
        c1,c2=st.columns([4,1]); c1.write(f"**{name}** — {'PASSED' if info['passed'] else 'NOT PASSED'}")
        if c2.button("Repeal Law" if info["passed"] else "Pass Law",key=f"law_{name}",use_container_width=True): game.toggle_law(name); st.rerun()


def render_immigration(game):
    opts=["Closed Borders (0/mo)","Low (15k/mo)","Moderate (35k/mo)","High (75k/mo)","Massive Open (150k/mo)"]
    current=opts.index(game.immigration_policy.get()); choice=st.radio("Set Monthly Net Overseas Migration Quota:",opts,index=current)
    if choice != game.immigration_policy.get(): game.immigration_policy.set(choice); game.recalculate_economy(); st.rerun()


def render_trade(game):
    c1,c2=st.columns(2)
    if c1.button("Enact Broad Tariffs (3 Months)",use_container_width=True): game.enact_tariffs(); st.rerun()
    if c2.button("Toggle Hard Sanctions",use_container_width=True): game.toggle_sanctions(); st.rerun()
    st.subheader("Resource Export Levies (%)")
    for res,var in game.resource_levies.items(): slider_set(f"Export Levy - {res}:",var,0,30,step=0.5)
    st.subheader("Import Tariffs (%)")
    for country,var in game.tariffs.items(): slider_set(f"Tariff - {country}:",var,0,30,step=0.5)
    game.recalculate_economy()


def render_market(game):
    rows=[]
    for comm,data in game.market_prices.items(): rows.append({"Resource / Commodity":comm,"Unit Measurement":data["unit"],"Current Price (AUD)":f"${data['current']:.3f}" if data['current']<1 else f"${data['current']:.2f}","Base Price (AUD)":f"${data['base']:.3f}" if data['base']<1 else f"${data['base']:.2f}","Base Demand (%)":f"{data.get('base_demand',100):.0f}%","Demand (%)":f"{data.get('demand',100):.1f}%"})
    st.dataframe(rows,use_container_width=True,hide_index=True)


def render_news(game):
    if not game.news_text.text:
        st.info("No news available yet. Advance a month to see updates.")
    else:
        st.text(game.news_text.text)


def render_election(game):
    e=st.session_state.get("election")
    if not e: return
    st.markdown('<div class="overlay"><h2>36-MONTH NATIONAL ELECTION DEBATE</h2></div>',unsafe_allow_html=True)
    avg_h=e["avg_happ"]; avg_c=e["avg_crime"]
    st.write(f"Term Avg Public Happiness: {avg_h:.1f}%  ")
    st.write(f"Months Happiness > 75%: {game.months_happy_over_75}")
    st.write(f"Ending Happiness: {game.happiness:.1f}%")
    st.write(f"Term Avg Crime Index: {avg_c:.1f}/100")
    st.write(f"Declared Wars This Term: {game.player_declared_wars_this_term}")
    st.write(f"Unemployment: {game.unemployment:.1f}% | Debt: ${game.debt:.1f}B AUD")
    st.radio("Select your core debate opening message to voters:",["Focus on Fiscal Responsibility & Economic Growth","Focus on Healthcare, Social Welfare & Community First","Focus on Law & Order, Strong Borders & National Security"],key="debate_msg")
    if st.button("COUNT ELECTION VOTES",type="primary",use_container_width=True):
        if game.term_count==1: won=avg_h>25.0 and game.months_happy_over_75>=10 and game.happiness>=50.0 and avg_c<40.0 and game.player_declared_wars_this_term<=1
        else: won=avg_h>25.0 and game.happiness>=50.0 and avg_c<40.0 and game.player_declared_wars_this_term<=3
        if won:
            st.success("ELECTION VICTORY! The people have re-elected you!")
            if st.button("Begin Next Term",use_container_width=True):
                game.term_count+=1; game.term_month=0; game.in_election=False; st.session_state["election"]=None; st.rerun()
        else:
            st.error("ELECTION DEFEAT! You lost the Election.")
            if st.button("Quit",use_container_width=True): game.return_to_main_menu(); st.rerun()


def app():
    st.set_page_config(page_title="Australian Federal Command",layout="wide",initial_sidebar_state="collapsed")
    st.markdown("""<style>
    html, body, [class*="css"] { font-family: Helvetica, Arial, sans-serif; }
    .topbar { background:#002B49; color:#FFC72C; padding:12px 18px; border-radius:4px; font-size:20px; margin-bottom:10px; }
    .hero, .overlay { background:#002B49; color:white; border:4px solid #002B49; border-radius:6px; padding:28px; text-align:center; margin:12px 0; }
    .hero { color:#FFC72C; font-size:26px; font-weight:700; }
    .subtitle { color:white; font-size:18px; margin-top:8px; }
    .overlay h2 { color:#FFC72C; }
    section[data-testid="stSidebar"] { display:none; }
    </style>""",unsafe_allow_html=True)
    _init_game(); game=st.session_state["game"]
    if not st.session_state.get("game_started",False): render_party_screen(game); return
    render_header(game)
    st.divider()
    if not game.in_election and not game.in_event and not st.session_state.get("overlay") and not st.session_state.get("confirmation") and not st.session_state.get("target_select"):
        if st.button("ADVANCE MONTH ▶",type="primary",use_container_width=True): game.advance_month(); st.rerun()
    tabs=st.tabs(["💰 Budget & Taxes","🏭 Industry & Energy","⚔️ Military & War","📜 Passing Laws","🛂 Immigration","🌐 Trade & Tariffs","📈 Market","🗞️ News"])
    with tabs[0]: render_budget(game)
    with tabs[1]: render_facilities(game)
    with tabs[2]: render_war(game)
    with tabs[3]: render_laws_tab(game)
    with tabs[4]: render_immigration(game)
    with tabs[5]: render_trade(game)
    with tabs[6]: render_market(game)
    with tabs[7]: render_news(game)
    render_target_select(game)
    render_confirmation(game)
    render_overlay(game)
    if game.in_election: render_election(game)
    # Streamlit notifications generated by the preserved simulation/messagebox compatibility layer.
    notes=st.session_state.get("notifications",[])
    if notes:
        for level,title,msg in notes[-3:]:
            getattr(st, {"info":"info","warning":"warning","error":"error"}.get(level,"info"))(f"{title}: {msg}")
        st.session_state["notifications"]=[]

if __name__ == "__main__":
    app()
