import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

class Severity(Enum):
    NORMAL = "Normal"
    MILD = "Mild"
    MODERATE = "Moderate"
    MODERATELY_SEVERE = "Moderately Severe"
    SEVERE = "Severe"
    VERY_SEVERE = "Very Severe"

class Pattern(Enum):
    NORMAL = "Normal"
    OBSTRUCTIVE = "Obstructive"
    RESTRICTIVE = "Restrictive"
    MIXED = "Mixed"

@dataclass
class PFTInterpretation:
    pattern: Pattern
    severity: Severity
    bronchodilator_response: bool
    reversible: bool
    fev1_severity: Severity
    fvc_severity: Severity
    clinical_impression: str
    recommendations: List[str]
    z_scores: Dict[str, float]
    percentiles: Dict[str, float]
    confidence_score: int 

class PFTInterpreter:
    
    def __init__(self):
        self.gli_coefficients = self._load_gli_coefficients()
    
    def _load_gli_coefficients(self) -> Dict:
        return {
            'caucasian': {
                'male': {
                    'fev1': {'intercept': -7.9776, 'ln_height': 1.8962, 'ln_age': -0.1847, 'spline_coeff': [0.1973, -0.1918, 0.1898]},
                    'fvc': {'intercept': -8.2996, 'ln_height': 2.0042, 'ln_age': -0.1735, 'spline_coeff': [0.1912, -0.1845, 0.1776]}
                },
                'female': {
                    'fev1': {'intercept': -7.3447, 'ln_height': 1.6982, 'ln_age': -0.1584, 'spline_coeff': [0.1854, -0.1789, 0.1723]},
                    'fvc': {'intercept': -7.8974, 'ln_height': 1.9058, 'ln_age': -0.1492, 'spline_coeff': [0.1798, -0.1734, 0.1667]}
                }
            }
        }
    
    def _calculate_confidence_score(self, pattern: Pattern, severity: Severity, z_scores: Dict[str, float]) -> int:
        base_score = 100
        lln_threshold = -1.645
        
        if pattern == Pattern.MIXED:
            base_score -= 20

        if severity == Severity.MILD:
            base_score -= 25

        if severity == Severity.MODERATE:
            base_score -= 10
            
        for key in ['fev1_fvc_z', 'fvc_z']:
            z_value = z_scores.get(key, 0)
            if lln_threshold - 0.3 < z_value < lln_threshold + 0.3:
                base_score -= 15
                break

        return max(50, min(99, int(base_score)))
    
    def calculate_predicted_values(self, age: int, height_cm: float, sex: str) -> Dict[str, float]:
        sex_key = 'male' if sex.upper() == 'M' else 'female'
        coeffs = self.gli_coefficients['caucasian'][sex_key]
        
        ln_height = math.log(height_cm / 100)
        ln_age = math.log(age)
        
        spline_value = self._calculate_spline(age)
        
        fev1_pred = math.exp(
            coeffs['fev1']['intercept'] + 
            coeffs['fev1']['ln_height'] * ln_height + 
            coeffs['fev1']['ln_age'] * ln_age + 
            spline_value
        )
        
        fvc_pred = math.exp(
            coeffs['fvc']['intercept'] + 
            coeffs['fvc']['ln_height'] * ln_height + 
            coeffs['fvc']['ln_age'] * ln_age + 
            spline_value
        )
        
        return {
            'fev1_predicted': fev1_pred,
            'fvc_predicted': fvc_pred,
            'fev1_fvc_predicted': fev1_pred / fvc_pred
        }
    
    def _calculate_spline(self, age: int) -> float:
        if age < 10:
            return 0.15 - (age - 3) * 0.02
        elif age < 20:
            return -0.05 + (age - 10) * 0.01
        elif age < 40:
            return 0.05 - (age - 20) * 0.001
        elif age < 60:
            return 0.03 - (age - 40) * 0.002
        else:
            return -0.01 - (age - 60) * 0.003
    
    def calculate_z_scores(self, measured: Dict, predicted: Dict, age: int, sex: str) -> Dict[str, float]:
        cv_fev1 = self._get_coefficient_variation('fev1', age, sex)
        cv_fvc = self._get_coefficient_variation('fvc', age, sex)
        
        z_fev1 = (measured['fev1'] - predicted['fev1_predicted']) / (predicted['fev1_predicted'] * cv_fev1)
        z_fvc = (measured['fvc'] - predicted['fvc_predicted']) / (predicted['fvc_predicted'] * cv_fvc)
        
        return {
            'fev1_z': z_fev1,
            'fvc_z': z_fvc,
            'fev1_fvc_z': self._calculate_ratio_z_score(measured['fev1_fvc_ratio'], predicted['fev1_fvc_predicted'])
        }
    
    def _get_coefficient_variation(self, parameter: str, age: int, sex: str) -> float:
        base_cv = 0.12 if parameter == 'fev1' else 0.11
        
        if age < 10:
            return base_cv + 0.04
        elif age < 20:
            return base_cv + 0.02
        elif age > 60:
            return base_cv + 0.05
        else:
            return base_cv
    
    def _calculate_ratio_z_score(self, measured_ratio: float, predicted_ratio: float) -> float:
        ratio_sd = 0.07
        return (measured_ratio/100 - predicted_ratio) / ratio_sd
    
    def determine_pattern(self, z_scores: Dict[str, float], fev1_fvc_ratio: float, fev1_percent: float, fvc_percent: float) -> Pattern:
        fev1_fvc_lln = z_scores['fev1_fvc_z'] < -1.645
        fvc_low = z_scores['fvc_z'] < -1.645
        fev1_low = z_scores['fev1_z'] < -1.645
        
        if fev1_fvc_lln:
            if fvc_low and fev1_low:
                return Pattern.MIXED
            else:
                return Pattern.OBSTRUCTIVE
        elif fvc_low and not fev1_fvc_lln:
            return Pattern.RESTRICTIVE
        else:
            return Pattern.NORMAL
    
    def determine_severity(self, fev1_percent: float, pattern: Pattern) -> Severity:
        if pattern == Pattern.NORMAL:
            return Severity.NORMAL
        
        if pattern == Pattern.OBSTRUCTIVE:
            if fev1_percent >= 80:
                return Severity.MILD
            elif fev1_percent >= 50:
                return Severity.MODERATE
            elif fev1_percent >= 30:
                return Severity.MODERATELY_SEVERE
            else:
                return Severity.SEVERE
        
        elif pattern == Pattern.RESTRICTIVE:
            if fev1_percent >= 70:
                return Severity.MILD
            elif fev1_percent >= 60:
                return Severity.MODERATE
            elif fev1_percent >= 50:
                return Severity.MODERATELY_SEVERE
            else:
                return Severity.SEVERE
        
        else:
            if fev1_percent >= 60:
                return Severity.MODERATE
            elif fev1_percent >= 40:
                return Severity.MODERATELY_SEVERE
            else:
                return Severity.SEVERE
    
    def assess_bronchodilator_response(self, pre_fev1: float, post_fev1: float, pre_fvc: float, post_fvc: float) -> Tuple[bool, float]:
        fev1_change = post_fev1 - pre_fev1
        fvc_change = post_fvc - pre_fvc
        fev1_percent_change = (fev1_change / pre_fev1) * 100
        
        fev1_significant = fev1_percent_change > 12 and fev1_change > 0.2
        fvc_significant = (fvc_change / pre_fvc) * 100 > 12 and fvc_change > 0.2
        
        return fev1_significant or fvc_significant, fev1_percent_change
    
    def generate_clinical_impression(self, interpretation: Dict) -> str:
        pattern = interpretation['pattern']
        severity = interpretation['severity']
        reversible = interpretation['reversible']
        
        impression_parts = []
        
        if pattern == Pattern.NORMAL:
            impression_parts.append("Pulmonary function testing demonstrates normal spirometric values.")
        
        elif pattern == Pattern.OBSTRUCTIVE:
            impression_parts.append(f"Spirometry reveals an obstructive ventilatory pattern with {severity.value.lower()} severity.")
            if reversible:
                impression_parts.append("Significant bronchodilator response suggests reversible airway obstruction, consistent with asthma or asthmatic component.")
            else:
                impression_parts.append("Limited bronchodilator response suggests fixed airway obstruction, more consistent with COPD.")
        
        elif pattern == Pattern.RESTRICTIVE:
            impression_parts.append(f"Spirometry demonstrates a restrictive pattern with {severity.value.lower()} severity.")
            impression_parts.append("Consider full pulmonary function testing with lung volumes to confirm restriction.")
        
        elif pattern == Pattern.MIXED:
            impression_parts.append(f"Spirometry shows a mixed ventilatory pattern with {severity.value.lower()} overall impairment.")
            impression_parts.append("Both obstructive and restrictive components are present.")
        
        return " ".join(impression_parts)
    
    
    def generate_recommendations(self, interpretation: Dict) -> List[str]:
        recommendations = []
        pattern = interpretation['pattern']
        severity = interpretation['severity']
        reversible = interpretation['reversible']
        
        if pattern == Pattern.NORMAL:
            recommendations.append("Continue routine health maintenance")
            recommendations.append("Consider repeat testing if symptoms develop")
        
        elif pattern == Pattern.OBSTRUCTIVE:
            if reversible:
                recommendations.append("Consider bronchodilator therapy trial")
                recommendations.append("Evaluate for asthma management")
                recommendations.append("Consider allergy testing if appropriate")
            else:
                recommendations.append("Evaluate for COPD management")
                recommendations.append("Consider smoking cessation counseling if applicable")
                recommendations.append("Pneumococcal and influenza vaccination")
            
            if severity in [Severity.MODERATE, Severity.MODERATELY_SEVERE, Severity.SEVERE]:
                recommendations.append("Pulmonology referral recommended")
                recommendations.append("Consider arterial blood gas analysis")
        
        elif pattern == Pattern.RESTRICTIVE:
            recommendations.append("Complete PFTs with lung volumes and DLCO")
            recommendations.append("Chest imaging if not recently performed")
            recommendations.append("Consider interstitial lung disease evaluation")
            if severity != Severity.MILD:
                recommendations.append("Pulmonology referral recommended")
        
        elif pattern == Pattern.MIXED:
            recommendations.append("Complete PFTs with lung volumes and DLCO")
            recommendations.append("Pulmonology referral recommended")
            recommendations.append("Consider CT chest for further evaluation")
        
        return recommendations
    
    def interpret_pft(self, pft_data: Dict) -> PFTInterpretation:
        demographics = pft_data['demographics']
        pre_bd = pft_data['pft_results']['pre_bronchodilator']
        post_bd = pft_data['pft_results']['post_bronchodilator']
        
        predicted = self.calculate_predicted_values(
            demographics['age'], 
            demographics['height_cm'], 
            demographics['sex']
        )
        
        measured_values = {
            'fev1': pre_bd['fev1']['liters'],
            'fvc': pre_bd['fvc']['liters'],
            'fev1_fvc_ratio': pre_bd['fev1_fvc_ratio']['value']
        }
        
        z_scores = self.calculate_z_scores(measured_values, predicted, demographics['age'], demographics['sex'])
        
        pattern = self.determine_pattern(
            z_scores, 
            pre_bd['fev1_fvc_ratio']['value'],
            pre_bd['fev1']['percent_predicted'],
            pre_bd['fvc']['percent_predicted']
        )
        
        severity = self.determine_severity(pre_bd['fev1']['percent_predicted'], pattern)
        
        bd_response, fev1_change = self.assess_bronchodilator_response(
            pre_bd['fev1']['liters'],
            post_bd['fev1']['liters'],
            pre_bd['fvc']['liters'],
            post_bd['fvc']['liters']
        )
        
        percentiles = {
            'fev1_percentile': self._z_to_percentile(z_scores['fev1_z']),
            'fvc_percentile': self._z_to_percentile(z_scores['fvc_z']),
            'fev1_fvc_percentile': self._z_to_percentile(z_scores['fev1_fvc_z'])
        }
        
        confidence = self._calculate_confidence_score(pattern, severity, z_scores)

        interpretation_dict = {
            'pattern': pattern,
            'severity': severity,
            'reversible': bd_response
        }
        
        clinical_impression = self.generate_clinical_impression(interpretation_dict)
        recommendations = self.generate_recommendations(interpretation_dict)
        
        return PFTInterpretation(
            pattern=pattern,
            severity=severity,
            bronchodilator_response=bd_response,
            reversible=bd_response,
            fev1_severity=self.determine_severity(pre_bd['fev1']['percent_predicted'], Pattern.OBSTRUCTIVE),
            fvc_severity=self.determine_severity(pre_bd['fvc']['percent_predicted'], Pattern.RESTRICTIVE),
            clinical_impression=clinical_impression,
            recommendations=recommendations,
            z_scores=z_scores,
            percentiles=percentiles,
            confidence_score=confidence
        )
    
    def _z_to_percentile(self, z_score: float) -> float:
        import math
        if z_score < -3:
            return 0.1
        elif z_score > 3:
            return 99.9
        else:
            percentile = 50 + 34.13 * z_score + 13.59 * (z_score**2 - 1) if abs(z_score) <= 2 else (
                99.7 if z_score > 0 else 0.3
            )
            return max(0.1, min(99.9, percentile))