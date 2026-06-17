# Scientific Rationale for Marine Heatwave Forecast Extension

> **Role of this doc:** the **conceptual foundation / "why"** for the forecast
> extension. Roadmap: `forecast-extension-plan.md`; bottom-state build plan:
> `forecast-implementation-document.md`; discovery: `catalog_report.md`.
> *Last refreshed 2026-06-17.*

## Purpose

This document provides the scientific justification for extending the Marine Heatwave Dashboard from a monitoring platform into a forecasting and fisheries decision-support platform.

It serves as the conceptual foundation for future development and ensures that implementation decisions remain aligned with fisheries management needs.

---

# Core Scientific Question

How can marine heatwave information be transformed into actionable information for fisheries scientists and fisheries managers?

The dashboard currently provides information about marine heatwaves.

The long-term objective is to provide information about climate risk.

---

# Current State

The existing dashboard is primarily a state-monitoring platform.

It answers questions such as:

* What is happening now?
* How unusual are current conditions?
* How does the current event compare with historical events?

The dashboard successfully implements:

* Marine heatwave detection
* Historical context
* Percentile rankings
* Regional comparisons
* Near-real-time monitoring

These capabilities are valuable for climate monitoring and situational awareness.

---

# Limitation of Surface-Based Monitoring

Most marine heatwave products focus on sea surface temperature (SST).

This approach is appropriate because:

* SST observations are widely available.
* SST is the basis of standard marine heatwave definitions.
* SST responds rapidly to atmospheric forcing.

However, many fisheries resources do not live at the surface.

Marine organisms experience environmental conditions throughout the water column.

Consequently:

Surface heatwaves and ecological heat stress are not always equivalent.

---

# Fisheries-Relevant Ocean States

The environmental variables experienced by marine organisms often include:

* Bottom temperature
* Shelf temperature
* Mixed-layer properties
* Stratification
* Sea ice conditions
* Cold pool extent
* Ocean heat content

These variables may be more directly connected to fisheries outcomes than SST alone.

---

# Alaska Motivation

The Alaska region provides a particularly strong justification for moving beyond surface conditions.

Key fisheries include:

* Snow crab
* Bristol Bay red king crab
* Pacific cod
* Walleye pollock
* Salmon

Many of these species respond strongly to bottom and shelf conditions.

---

# Snow Crab Example

Snow crab provides a motivating example.

Scientific studies have linked recent snow crab declines to:

* Elevated bottom temperatures
* Reduced cold-pool extent
* Altered habitat availability

These mechanisms operate near the seafloor rather than at the ocean surface.

Consequently:

Surface marine heatwave metrics may not fully capture environmental stress experienced by snow crab populations.

---

# Cold Pool Dynamics

The Eastern Bering Sea cold pool is among the most important environmental features in Alaska fisheries science.

The cold pool:

* Influences species distributions
* Structures predator-prey interactions
* Provides thermal refuge
* Serves as a key ecosystem indicator

Changes in cold-pool extent can have substantial ecological consequences.

For many management applications, cold-pool conditions may be more informative than SST anomalies.

---

# Why a regional ocean model (Bering10K ROMS / MOM6)?

Regional ocean models are not introduced because they are superior forecasting tools.

They are introduced because they provide access to ocean states that are unavailable
from SST products. Two are used, presented side-by-side as labelled options: **Bering10K
ROMS** (the ACLIM-validated Bering/EBS model) and **MOM6-COBALT-NEP10k** (the CEFI
model, with a public forecast arm). Where they disagree, the divergence is itself an
honest uncertainty signal.

Examples of the states they expose include:

* Bottom temperature
* Water-column temperature structure
* Ocean circulation
* Sea ice
* Ocean heat content

These variables create opportunities to develop fisheries-relevant climate indicators.

---

# Ocean States Versus Fisheries States

An important distinction exists between:

Ocean State Variables

and

Fisheries State Variables

Examples:

Ocean State Variables:

* SST
* Bottom temperature
* Sea ice
* Cold-pool extent

Fisheries State Variables:

* Recruitment
* Biomass
* Distribution
* Mortality

The dashboard is designed primarily around ocean-state variables.

The objective is not to forecast fish stocks.

Instead, the objective is to improve understanding of environmental risk.

---

# Climate Risk Framework

The dashboard follows a three-layer conceptual framework.

Layer 1

Ocean State

Examples:

* SST
* Bottom temperature
* Sea ice

Layer 2

Climate Events

Examples:

* Surface marine heatwaves
* Bottom marine heatwaves
* Cold-pool contraction

Layer 3

Climate Risk

Examples:

* Elevated habitat risk
* Increased thermal stress
* Increased ecosystem disruption potential

The dashboard currently operates primarily within Layers 1 and 2.

Future development expands into Layer 3.

---

# Forecasting Philosophy

The project does not seek to compete with NOAA climate-model development efforts.

Forecast generation should leverage existing operational products whenever possible.

Examples include:

* NOAA PSL
* NMME
* ECMWF
* NOAA MOM6
* NOAA CEFI

The first forecasting capability is intentionally lightweight: a statistical
short-term sea-surface-temperature forecast (persistence, damped persistence,
AR(1)) built on the existing OISST pipeline. This is an honest, low-risk entry
into Stage 2 — and the bar that any later dynamical or seasonal product must beat.

Forecasts are produced from the primitive at the grid level. The temperature
anomaly is forecast per grid cell and converted to a marine-heatwave exceedance
probability against the existing 90th-percentile threshold, and only then
aggregated to regional and area-based products. The monitoring aggregates built
for situational awareness do not constrain the forecast.

The same forecast machinery is variable-agnostic. It forecasts an anomaly field
against a threshold field, so the same engine serves surface temperature today and
bottom temperature or seasonal ensembles later, without redevelopment.

The dashboard's role is scientific synthesis and communication.

Its comparative advantage is:

Complex scientific products

→

Accessible climate-risk information

---

# Decision-Support Philosophy

The ultimate objective is not forecasting.

The ultimate objective is preparedness.

Marine heatwave forecasts are valuable because they create preparation windows.

Preparation windows allow:

* Monitoring plans
* Survey planning
* Ecosystem assessment
* Risk communication
* Adaptive management

The dashboard should therefore be evaluated based on whether it improves preparedness rather than forecast skill alone.

---

# Relationship to Ecosystem Report Cards

Ecosystem report cards typically summarize recent environmental conditions.

The dashboard seeks to extend this framework by adding:

* Historical context
* Environmental rankings
* Climate-event detection
* Forecast probabilities
* Risk indicators

The long-term objective is to support annual ecosystem assessments and climate-ready fisheries management.

---

# Long-Term Vision

The dashboard evolves through four stages.

Stage 1

Environmental Monitoring

Current status.

Stage 2

Environmental Forecasting

Forecast extension. Entered first via statistical short-term SST forecasting on
the existing pipeline, with bottom-ocean-state and seasonal forecasts as
subsequent extensions of the same variable-agnostic engine.

Stage 3

Climate Risk Assessment

Risk indicators.

Stage 4

Climate-Informed Decision Support

Management-relevant products.

The project currently focuses on the transition from Stage 1 to Stage 2 while laying the scientific foundation for Stages 3 and 4.

---

# Guiding Principle

The dashboard should always prioritize scientific usefulness over technical sophistication.

The objective is not to build increasingly complex models.

The objective is to provide fisheries scientists and managers with information that improves understanding, preparedness, and decision making under climate variability and marine heatwave risk.
