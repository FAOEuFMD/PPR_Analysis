"""
calculations.py
Contains deterministic, unit-tested formulas for PPR dashboard.
"""
import logging

def vaccinated_initial(population, coverage):
    """
    Calculate initial animals to vaccinate.
    Formula: vaccinated_initial = population * coverage
    """
    result = population * coverage
    logging.info(f"vaccinated_initial: {population} * {coverage} = {result}")
    return result

def doses_required(vaccinated_initial, wastage):
    """
    Calculate effective doses required accounting for wastage.
    Formula: doses_required = vaccinated_initial * (1 + wastage)
    """
    result = vaccinated_initial * (1 + wastage)
    logging.info(f"doses_required: {vaccinated_initial} * (1 + {wastage}) = {result}")
    return result

def cost_before_adj(doses_required, cost_per_animal):
    """
    Calculate cost before political and delivery multipliers.
    Formula: cost_before_adj = doses_required * cost_per_animal
    """
    result = doses_required * cost_per_animal
    logging.info(f"cost_before_adj: {doses_required} * {cost_per_animal} = {result}")
    return result

def political_multiplier(psi, thresholds=(0.4, 0.7), multipliers=(1.0, 1.5, 2.0)):
    """
    Calculate political stability multiplier.
    Default thresholds: (0.4, 0.7)
    Default multipliers: (1.0, 1.5, 2.0)
    """
    if psi < thresholds[0]:
        mult = multipliers[0]
    elif psi < thresholds[1]:
        mult = multipliers[1]
    else:
        mult = multipliers[2]
    logging.info(f"political_multiplier: PSI={psi}, mult={mult}")
    return mult

def delivery_channel_multiplier(channel, multipliers={"Public": 1.2, "Mixed": 1.0, "Private": 0.85}):
    """
    Get delivery channel multiplier.
    """
    mult = multipliers.get(channel, 1.0)
    logging.info(f"delivery_channel_multiplier: channel={channel}, mult={mult}")
    return mult

def newborns(species, vaccinated_initial, rates={"Goats": 0.6, "Sheep": 0.4}):
    """
    Estimate newborns for second year by species.
    """
    rate = rates.get(species, 0.5)
    result = vaccinated_initial * rate
    logging.info(f"newborns: species={species}, vaccinated_initial={vaccinated_initial}, rate={rate}, result={result}")
    return result

def second_year_coverage(newborns, coverage=1.0):
    """
    Coverage in year 2 (default 100% of newborns, editable).
    """
    result = newborns * coverage
    logging.info(f"second_year_coverage: newborns={newborns}, coverage={coverage}, result={result}")
    return result

def total_cost(cost_before_adj, political_mult, delivery_mult):
    """
    Calculate total country-species cost.
    Formula: total_cost = cost_before_adj * political_mult * delivery_mult
    """
    result = cost_before_adj * political_mult * delivery_mult
    logging.info(f"total_cost: {cost_before_adj} * {political_mult} * {delivery_mult} = {result}")
    return result
