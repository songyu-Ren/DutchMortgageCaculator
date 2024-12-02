import numpy as np
import gradio as gr
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict
import matplotlib.ticker as mtick

# Utility function: Convert percentages to decimal for calculation
def convert_percentages_to_decimal(*rates: float) -> List[float]:
    """Converts percentage rates to decimal form for calculations."""
    return [rate / 100 for rate in rates]

# Loan calculation function
def calculate_loan_details(house_value: float, loan_percentage: float, loan_rate: float, loan_years: int, loan_type: str) -> Tuple[float, float, List[float]]:
    """Calculates loan details including down payment, loan amount, and monthly payments."""
    loan_amount = house_value * loan_percentage
    down_payment = house_value - loan_amount
    monthly_interest_rate = loan_rate / 12
    loan_term_months = loan_years * 12

    if loan_type == "Annuity":
        monthly_payment = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / \
                          ((1 + monthly_interest_rate) ** loan_term_months - 1)
        monthly_payments = [monthly_payment] * loan_term_months
    elif loan_type == "Linear":
        monthly_payments = [
            loan_amount / loan_term_months + loan_amount * monthly_interest_rate * (1 - (month - 1) / loan_term_months)
            for month in range(1, loan_term_months + 1)
        ]
    else:
        raise ValueError("Invalid loan type")

    return down_payment, loan_amount, monthly_payments

# Cumulative costs calculation
def calculate_cumulative_costs(house_value: float, initial_rent: float, rent_inflation_rate: float, appreciation_rate: float,
                               initial_maintenance_cost: float, maintenance_inflation_rate: float, monthly_payments: List[float],
                               max_sell_year: int, initial_investment: float) -> Tuple[List[float], List[float]]:
    """Calculates cumulative costs for renting and owning over a period of years."""
    renting_cumulative_costs = []
    owning_cumulative_costs = []
    cumulative_rent_cost = 0
    cumulative_owning_cost = initial_investment

    for year in range(1, max_sell_year + 1):
        annual_rent = initial_rent * (1 + rent_inflation_rate) ** (year - 1)
        cumulative_rent_cost += annual_rent
        renting_cumulative_costs.append(cumulative_rent_cost)

        annual_maintenance_cost = initial_maintenance_cost * (1 + maintenance_inflation_rate) ** (year - 1)
        cumulative_owning_cost += sum(monthly_payments[(year - 1) * 12:year * 12]) + annual_maintenance_cost
        owning_cumulative_costs.append(cumulative_owning_cost)

    return renting_cumulative_costs, owning_cumulative_costs

# Break-even year determination
def determine_break_even_year(renting_costs: List[float], owning_costs: List[float], years: List[int]) -> int:
    """Determines the break-even year where owning becomes cheaper than renting."""
    for i, (rent_cost, own_cost) in enumerate(zip(renting_costs, owning_costs)):
        if own_cost < rent_cost:
            return years[i]
    return None

def calculate_post_sale_raw_cash(house_value: float, appreciation_rate: float, sell_tax_rate: float, years: List[int]) -> List[float]:
    """Calculates the post-sale cash on hand after selling the property."""
    post_sale_cash = []
    for year in years:
        property_value = house_value * (1 + appreciation_rate) ** (year-1)
        profit = property_value - house_value
        sell_after_tax = property_value - profit * sell_tax_rate
        post_sale_cash.append(sell_after_tax)
    return post_sale_cash

# Post-sale cash calculation
def calculate_post_sale_cash(house_value: float, appreciation_rate: float, sell_tax_rate: float, owning_costs: List[float], years: List[int]) -> Dict[str, float]:
    """Calculates the post-sale cash on hand after selling the property."""
    post_sale_cash = {}
    for year in years:
        property_value = house_value * (1 + appreciation_rate) ** year
        profit = property_value - house_value
        sell_tax = profit * sell_tax_rate
        net_cash_after_sale = property_value - owning_costs[year - 1] - sell_tax
        post_sale_cash[str(year)] = round(net_cash_after_sale, 2)
    return post_sale_cash

def plot_results(years: List[int], renting_costs: List[float], owning_costs: List[float], break_even_year: int, title: str) -> str:
    """Generates a plot of the cumulative costs for renting and owning."""
    plt.figure(figsize=(10, 6))
    plt.plot(years, renting_costs, label="Cumulative Rent Cost", linestyle='--')
    plt.plot(years, owning_costs, label="Cumulative Buying Cost", linestyle='-')
    if break_even_year is not None:
        plt.axvline(x=break_even_year, color='grey', linestyle=':', label=f'Break-even Year: {break_even_year}')
    plt.xlabel('Year')
    plt.ylabel('Cumulative Cost (€)')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    
    # Disable scientific notation for the entire plot
    plt.ticklabel_format(style='plain', axis='y')

    # Add thousand separators for better readability
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))

    plt_path = f"{title.replace(' ', '_').lower()}.png"
    plt.savefig(plt_path)
    plt.close()
    return plt_path

# Overall cash flow analysis
def calculate_cash_flow_analysis(annual_salary: float, salary_growth_rate: float, opportunity_cost_rate: float,
                                 monthly_payments: List[float], initial_rent: float, rent_inflation_rate: float, max_years: int,
                                 initial_investment: float, maintenance_costs: List[float], annual_expenditure: float, sale_after_tax: List[float],
                                 which_year_to_sell: int) -> Tuple[List[float], List[float], List[float]]:
    """Calculates the overall cash flow analysis for renting and buying."""
    cumulative_cash_rent = []
    cumulative_cash_buy = []
    cumulative_cash_buy_and_sell = []
    cash_rent = initial_investment
    cash_buy = initial_investment
    for year in range(1, max_years + 1):
        annual_salary *= (1 + salary_growth_rate)
        net_savings = annual_salary - annual_expenditure

        rent_cost = initial_rent * (1 + rent_inflation_rate) ** (year - 1)
        cash_rent += net_savings - rent_cost
        cash_rent *= (1 + opportunity_cost_rate)
        cumulative_cash_rent.append(cash_rent)

        total_buy_cost = sum(monthly_payments[(year - 1) * 12:year * 12]) + maintenance_costs[year - 1]
        cash_buy += net_savings - total_buy_cost
        cash_buy *= (1 + opportunity_cost_rate)
        cumulative_cash_buy.append(cash_buy)
        if year<which_year_to_sell:
            cumulative_cash_buy_and_sell.append(cash_buy)
        elif year==which_year_to_sell:
            cash = cash_buy + sale_after_tax[year-1]
            cash -= sum(monthly_payments[year * 12:]) # pay off the remaining mortgage
            cumulative_cash_buy_and_sell.append(cash)
        else: # year>which_year_to_sell
            cash_buy_and_sell = cumulative_cash_buy_and_sell[-1] + net_savings - maintenance_costs[year - 1]
            cash_buy_and_sell *= (1 + opportunity_cost_rate)
            cumulative_cash_buy_and_sell.append(cash_buy_and_sell)

    return cumulative_cash_rent, cumulative_cash_buy, cumulative_cash_buy_and_sell

# Full Gradio app implementation
def analysis_handler(mode, house_value, loan_percentage, loan_rate_percentage, loan_years, appreciation_rate_percentage,
                     initial_maintenance_cost, maintenance_inflation_rate_percentage, initial_rent,
                     rent_inflation_rate_percentage, sell_tax_rate_percentage, max_years, initial_investment,
                     annual_salary, salary_growth_rate_percentage,
                     opportunity_cost_rate_percentage, annual_expenditure, which_year_to_sell, mortgage_type):
    """Handles the analysis based on the selected mode and input parameters."""

    # Convert percentages to decimal
    appreciation_rate, rent_inflation_rate, maintenance_inflation_rate, loan_rate, sell_tax_rate, salary_growth_rate, opportunity_cost_rate = convert_percentages_to_decimal(
        appreciation_rate_percentage, rent_inflation_rate_percentage, maintenance_inflation_rate_percentage,
        loan_rate_percentage, sell_tax_rate_percentage, salary_growth_rate_percentage,
        opportunity_cost_rate_percentage
    )

    # Loan details calculation
    down_payment, loan_amount, monthly_payments = calculate_loan_details(
        house_value, loan_percentage, loan_rate, loan_years, mortgage_type
    )

    # Analysis based on the mode
    if mode == "Break-even Analysis":
        renting_costs, owning_costs = calculate_cumulative_costs(
            house_value, initial_rent, rent_inflation_rate, appreciation_rate, initial_maintenance_cost,
            maintenance_inflation_rate, monthly_payments, max_years, initial_investment
        )
        years = list(range(1, max_years + 1))
        break_even_year = determine_break_even_year(renting_costs, owning_costs, years)
        post_sale_cash = calculate_post_sale_cash(house_value, appreciation_rate, sell_tax_rate, owning_costs, years)
        plot_path = plot_results(years, renting_costs, owning_costs, break_even_year, "Break-even Analysis")

        return plot_path, {
            "Break-even Year": break_even_year,
            "Cumulative Rent Costs": renting_costs,
            "Cumulative Buying Costs": owning_costs,
            "Post-sale Cash on Hand": post_sale_cash
        }

    elif mode == "Overall Cash Flow Analysis":
        maintenance_costs = [
            initial_maintenance_cost * (1 + maintenance_inflation_rate) ** year for year in range(max_years)
        ]
        sale_after_tax = calculate_post_sale_raw_cash(house_value, appreciation_rate, sell_tax_rate, list(range(1, max_years + 1)))
        cash_rent, cash_buy, cash_buy_and_sell = calculate_cash_flow_analysis(
            annual_salary, salary_growth_rate, opportunity_cost_rate, monthly_payments,
            initial_rent, rent_inflation_rate, max_years, initial_investment, maintenance_costs, annual_expenditure, sale_after_tax, which_year_to_sell
        )

        # Plot cash flow results with updated colors and markers
        fig, ax = plt.subplots(figsize=(10, 6))

        # Line 1: Renting, blue color with circular markers
        ax.plot(
            range(1, max_years + 1), 
            cash_rent, 
            label="Cumulative Cash (Renting)", 
            linestyle="--", 
            color="blue", 
            marker="o", 
            linewidth=2
        )

        # Line 2: Buying, red color with square markers
        ax.plot(
            range(1, max_years + 1), 
            cash_buy, 
            label="Cumulative Cash (Buying)", 
            linestyle="-", 
            color="red", 
            marker="s", 
            linewidth=2
        )

        # Line 3: Buying + Selling, yellow color with triangle markers
        ax.plot(
            range(1, max_years + 1), 
            cash_buy_and_sell, 
            label="Cumulative Cash (Buying + Selling)", 
            linestyle=":", 
            color="green", 
            marker="^", 
            linewidth=2
        )

        # Axis labels and title
        ax.set_xlabel("Year")
        ax.set_ylabel("Cumulative Cash (€)")
        ax.set_title("Overall Cash Flow Analysis")

        # Add legend with improved visibility
        ax.legend(title="Cumulative Cash Flows", loc="upper left", fontsize="medium")

        # Add grid for readability
        ax.grid(True)

        # Save and close the figure
        plt_path = "cash_flow_analysis.png"
        fig.savefig(plt_path)
        plt.close(fig)

        return plt_path, {
            "Cumulative Cash (Renting)": cash_rent,
            "Cumulative Cash (Buying)": cash_buy,
            "Cumulative Cash (Buying + Selling)": cash_buy_and_sell
        }

# Gradio interface
with gr.Blocks() as demo:
    mode = gr.Radio(["Break-even Analysis", "Overall Cash Flow Analysis"], label="Mode", value="Break-even Analysis")

    inputs = [
        gr.Slider(100000, 1000000, step=1000, label="House Value (€)", value=300000),
        gr.Slider(0, 1, step=0.01, label="Loan Percentage", value=0.7),
        gr.Slider(0.1, 10, step=0.1, label="Loan Interest Rate (%)", value=3.7),
        gr.Slider(1, 50, step=1, label="Loan Term (Years)", value=20),
        gr.Slider(0, 20, step=0.1, label="Appreciation Rate (%)", value=2),
        gr.Slider(0, 10000, step=100, label="Initial Maintenance Cost (€)", value=1000),
        gr.Slider(0, 10, step=0.1, label="Maintenance Inflation Rate (%)", value=2),
        gr.Slider(0, 100000, step=100, label="Initial Rent (€)", value=15000),
        gr.Slider(0, 10, step=0.1, label="Annual Rent Inflation Rate (%)", value=2),
        gr.Slider(0, 50, step=0.1, label="Sell Tax Rate (%)", value=36),
        gr.Slider(1, 100, step=1, label="Maximum Years", value=30),
        gr.Slider(0, 50000, step=500, label="Initial Investment (€)", value=5000),
        gr.Slider(30000, 200000, step=1000, label="Annual Salary (€)", value=60000),
        gr.Slider(0, 10, step=0.1, label="Annual Salary Growth Rate (%)", value=2),
        gr.Slider(0, 10, step=0.1, label="Opportunity Cost Rate (%)", value=1),
        gr.Slider(0, 150000, step=500, label="Annual Expenditure (€)", value=15000),
        gr.Slider(0, 30, step=1, label="Which year to sell", value=10),
        gr.Radio(["Annuity", "Linear"], label="Mortgage Type", value="Annuity")
    ]

    outputs = [
        gr.Image(label="Analysis Chart"),
        gr.JSON(label="Analysis Data")
    ]

    gr.Interface(
        fn=analysis_handler,
        inputs=[mode] + inputs,
        outputs=outputs,
        title="Buy vs Rent Analysis Tool",
        description="Switch between break-even analysis and overall cash flow analysis.",
        live=True
    )

demo.launch(share=True)