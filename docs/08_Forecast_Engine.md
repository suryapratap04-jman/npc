# 08. Forecast Engine

This document describes the Forecast Engine's supply and demand capacity scenario calculations.

## 1. Roll-Forward Calculations
The Forecast Engine simulates allocations over a 6-month timeline:
- **Supply Capacity**: The cumulative active employee hours, adjusted for planned exits/resignations.
- **Demand Load**: Calculated by summing current active project allocations and CRM pipeline opportunities multiplied by expected close probability.
- **Deficit/Surplus**: Generates deficit indicators when demand exceeds supply.

## 2. What-If Scenarios
The dashboard allows interactive parameter updates:
- **Adjust pipeline close probability threshold** (e.g., only include deals with >80% close probability).
- **Hiring scenarios**: Simulate adding headcounts in specific competencies.
