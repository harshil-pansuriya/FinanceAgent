import React, { useState } from 'react';
import { formatCurrency } from '../../utils/helpers';

const Charts = ({ insights }) => {
    const [hoveredSlice, setHoveredSlice] = useState(null);

    if (!insights || !insights.category_analysis || insights.category_analysis.length === 0) {
        return (
            <div className="charts-placeholder">
                <div className="placeholder-content">
                    <span className="placeholder-icon">📊</span>
                    <h4>No data available for charts</h4>
                    <p>Add some transactions to see visual analytics</p>
                </div>
            </div>
        );
    }

    // Enhanced pie chart with animations and interactions
    const PieChart = ({ data, title }) => {
        const total = data.reduce((sum, item) => sum + item.amount, 0);
        let cumulativePercentage = 0;
        
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ];

        return (
            <div className="pie-chart-container-small">
                <div className="chart-header-small">
                    <h6>{title}</h6>
                    <div className="chart-total-small">
                        Total: {formatCurrency(total)}
                    </div>
                </div>
                <div className="pie-chart-layout">
                    <div className="pie-chart-small">
                        <svg viewBox="0 0 200 200" className="pie-svg-small">
                            {data.map((item, index) => {
                                const percentage = (item.amount / total) * 100;
                                const angle = (percentage / 100) * 360;
                                const startAngle = cumulativePercentage * 3.6;
                                const endAngle = startAngle + angle;
                                
                                const x1 = 100 + 70 * Math.cos((startAngle - 90) * Math.PI / 180);
                                const y1 = 100 + 70 * Math.sin((startAngle - 90) * Math.PI / 180);
                                const x2 = 100 + 70 * Math.cos((endAngle - 90) * Math.PI / 180);
                                const y2 = 100 + 70 * Math.sin((endAngle - 90) * Math.PI / 180);
                                
                                const largeArcFlag = angle > 180 ? 1 : 0;
                                const pathData = `M 100 100 L ${x1} ${y1} A 70 70 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
                                
                                cumulativePercentage += percentage;
                                
                                return (
                                    <path
                                        key={index}
                                        d={pathData}
                                        fill={colors[index % colors.length]}
                                        className={`pie-slice-small ${hoveredSlice === index ? 'hovered' : ''}`}
                                        onMouseEnter={() => setHoveredSlice(index)}
                                        onMouseLeave={() => setHoveredSlice(null)}
                                        style={{
                                            transition: 'all 0.3s ease',
                                            cursor: 'pointer'
                                        }}
                                    />
                                );
                            })}
                        </svg>
                        <div className="pie-chart-center-small">
                            {hoveredSlice !== null ? (
                                <div className="hover-info-small">
                                    <div className="hover-category-small">{data[hoveredSlice].category}</div>
                                    <div className="hover-amount-small">{formatCurrency(data[hoveredSlice].amount)}</div>
                                    <div className="hover-percentage-small">
                                        {((data[hoveredSlice].amount / total) * 100).toFixed(1)}%
                                    </div>
                                </div>
                            ) : (
                                <div className="center-info-small">
                                    <div className="center-label-small">Total</div>
                                    <div className="center-amount-small">{formatCurrency(total)}</div>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="pie-legend-small">
                        {data.map((item, index) => (
                            <div 
                                key={index} 
                                className={`legend-item-small ${hoveredSlice === index ? 'highlighted' : ''}`}
                                onMouseEnter={() => setHoveredSlice(index)}
                                onMouseLeave={() => setHoveredSlice(null)}
                            >
                                <div 
                                    className="legend-color-small" 
                                    style={{ backgroundColor: colors[index % colors.length] }}
                                />
                                <div className="legend-content-small">
                                    <span className="legend-label-small">{item.category}</span>
                                    <span className="legend-value-small">
                                        {formatCurrency(item.amount)}
                                    </span>
                                    <span className="legend-percentage-small">
                                        {((item.amount / total) * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    };





    return (
        <div className="charts-small">
            <div className="charts-header-small">
                <h5>📊 Spending Distribution</h5>
            </div>
        
            <div className="charts-grid-small">
                <div className="chart-card-small">
                    <PieChart 
                        data={insights.category_analysis} 
                        title="Category Breakdown"
                    />
                </div>
            </div>
        </div>
    );
};

export default Charts;