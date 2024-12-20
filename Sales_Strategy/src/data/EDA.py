import matplotlib.pyplot as plt
import seaborn as sns   
import pandas as pd
import numpy as np

# Read in the data 
sales = pd.read_csv('../../data/processed/sales_data_clean.csv')
sales.head() # inspect first rows
sales.dtypes # check column types
sales['sales_method'].unique() # As expected, only three categories
sales['customer_id'].nunique() # every transaction is unique
sales.info() # no missing values

sales['years_as_customer'].describe()
# Some customers have been buying for longer than the company has been in business. 
sales[sales['years_as_customer'] > 40] # inspect these customers
sales = sales[sales['years_as_customer'] < 40] # remove these customers

sales.to_csv('../../data/processed/sales_data_clean.csv', index=False) # Save updated data

# ---------------------------------------- # 
#       Exploratory Data Analysis          # 
# ---------------------------------------- #

# Correlation matrix between variables. 

# Summary statistics by sales method
sales_by_method = sales.groupby('sales_method').agg(total_revenue=('revenue', 'sum'),
                                                    total_transactions=('revenue', 'count'),
                                                    avg_revenue=('revenue', 'mean'),
                                                    avg_nb_sold=('nb_sold', 'mean')).round(2) 

stats_by_method = sales.groupby('sales_method').agg({'revenue': ['mean', 'median', 'std'],
                                                     'nb_sold': ['mean', 'median', 'std']}).round(2) 

# Save summary statistics by sales method
stats_by_method.to_csv('../../reports/tables/summary_stats_by_sales_method.csv')   

# Visualise 
# Revenue by Sales Method
sns.violinplot(data=sales, x='sales_method', y='revenue')
plt.title('Revenue Distribution by Sales Method')
plt.xlabel('Sales Method')
plt.ylabel('Revenue')
plt.savefig('../../reports/figures/revenue_distribution_by_sales_method.png')

# Revenue by units sold
sns.violinplot(data=sales, x='sales_method', y='nb_sold')
plt.title('Number of Items Sold by Sales Method')
plt.xlabel('Sales Method')
plt.ylabel('Number of Items Sold')  
plt.savefig('../../reports/figures/nb_sold_distribution_by_sales_method.png')

# Top 10 states by sales count
sales['state'].value_counts().head(10).plot(kind='bar')
plt.title('Top 10 States by Sales')
plt.xlabel('State')
plt.ylabel('Number of Sales')
plt.savefig('../../reports/figures/top_10_states_by_sales.png', bbox_inches='tight')

# Top 10 states by total revenue 
Top_10_by_revenue = sales.groupby('state').agg(total_revenue=('revenue','sum'))
Top_10_by_revenue['total_revenue'].sort_values(ascending=False).head(10).plot(kind='bar')
plt.title('Top 10 States by Total Revenue')
plt.xlabel('State')
plt.ylabel('Total Revenue')
plt.legend().remove()
plt.savefig('../../reports/figures/top_10_states_by_revenue.png', bbox_inches='tight')

# Percentage of revenue by state 
Top_10_by_revenue['perc_of_total'] = Top_10_by_revenue['total_revenue'] / (Top_10_by_revenue['total_revenue'].sum())
Top_10_by_revenue.sort_values(by='total_revenue',ascending=False).head(10)    
    
# Average revenue per transaction over time
sales.groupby(['week', 'sales_method']).agg({'revenue':'mean'}).unstack().plot()
plt.title('Average Revenue per Transaction by Week')
plt.xlabel('Week')
plt.ylabel('Average Revenue')
plt.legend(['Call', 'Email', 'Email + Call'])
plt.savefig('../../reports/figures/avg_revenue_by_week.png')

# Average number of transactions per week by sales method
sales.groupby(['week', 'sales_method']).agg({'revenue':'count'}).unstack().plot()
plt.title('Number of Transactions per Week')
plt.legend(['Call', 'Email', 'Email + Call'])
plt.xlabel('Week')
plt.ylabel('Number of Transactions')    
plt.savefig('../../reports/figures/transactions_by_week.png')

# Data appears to not be normally distributed. 

# ------------------------------------------- # 
#           Customer Segmentation             #
# ------------------------------------------- # 

# Analise the distribution of years_as_customer
sns.displot(data=sales, x='years_as_customer')

# Group customers into 4 categories
# Define bins and labels
bins = [0, 2, 10, 20, 39]
labels = ['0-2 (New)', '3-10 (Growing)', '11-20 (Established)', '21-39 (Loyal)']

# Create the tenure group column
sales['tenure_group'] = pd.cut(sales['years_as_customer'], bins=bins, labels=labels)

# Visualize spread with a barplot 
sales.groupby('tenure_group').agg(n_customers=('years_as_customer','count')).plot(kind='bar')
plt.title('Number of Customers Per Tenure Group')
plt.xlabel('Tenure Group')
plt.ylabel('Number of Customers')
plt.xticks(rotation=45)
plt.legend().remove()
plt.savefig('../../reports/figures/n_customers_per_group.png', bbox_inches='tight')

# Revenue Generated by customer group
revenue_per_cust_per_met = sales.groupby(['tenure_group','sales_method']).agg(average_revenue=('revenue', 'mean'))
revenue_per_cust_per_met['average_revenue'] = revenue_per_cust_per_met['average_revenue'].round(2)
revenue_per_cust_per_met.to_csv('../../reports/tables/revenue_per_cust_per_met.csv')

sns.barplot(data=revenue_per_cust_per_met, x='tenure_group', y='average_revenue', hue='sales_method')
plt.title('Average Revenue by Tenure Group')
plt.xlabel('Tenure Group')
plt.ylabel('Average Revenue')
plt.legend(bbox_to_anchor=(1,1))
plt.savefig('../../reports/figures/avg_revenue_by_tenure.png',bbox_inches='tight')

# Is there a relationship between revenue and number of items sold?
sns.heatmap(sales[['revenue', 'nb_sold','week',
                   'years_as_customer','nb_site_visits']].corr(), annot=True)
plt.title('Correlation between Variables')
plt.savefig('../../reports/figures/correlation_heatmap.png',bbox_inches='tight')

# Yes, there is a positive correlation between revenue and number of items sold.

# ---------------------------------------- # 
# Test for normality 
# ---------------------------------------- # 

# Create additional column for revenue per item sold
sales['revenue_per_sale'] = sales['revenue'] / sales['nb_sold']

# Verify if new column 'revenue_per_sale' is normally distributed 
sns.violinplot(data=sales, x='sales_method', y='revenue_per_sale')
sns.histplot(data=sales[sales['sales_method'] == 'call'], x='revenue_per_sale',kde=True)

from scipy.stats import shapiro

# Shapiro-Wilk Test per sales_method
shapiro_results = []

# Loop through each sales method and perform the Shapiro-Wilk test
for method in sales['sales_method'].unique():
    stat, p_value = shapiro(sales[sales['sales_method'] == method]['revenue'])
    result = "Normally Distributed" if p_value > 0.05 else "Not Normally Distributed"
    
    # Append the results to the list as a dictionary
    shapiro_results.append({
        'sales_method': method,
        'p_value': p_value,
        'statistic': stat,
        'result': result
    })

# Convert the list of results into a Pandas DataFrame
shapiro_table = pd.DataFrame(shapiro_results)

# Display the table
print(shapiro_table)
    
sales.groupby('sales_method')['customer_id'].nunique()    

# Q-Q plot for each sales method

import scipy.stats as stats

for method in sales['sales_method'].unique():
    stats.probplot(sales[sales['sales_method'] == method]['revenue'], dist="norm", plot=plt)
    plt.title(f'Q-Q Plot for {method}: Revenue')
    plt.savefig(f'../../reports/figures/qq_plot_{method}_rps.png')
    plt.show()   

# Conclusion: Data isn't normally distributed, so we will use non-parametric tests.

sales.to_csv('../../data/interim/sales_data_HT.csv')