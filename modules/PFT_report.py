import json
from datetime import datetime
from typing import Dict, List
from dataclasses import asdict
from modules.PFT_interpreter import PFTInterpreter, PFTInterpretation, Pattern, Severity

class PFTReportGenerator:
    
    def __init__(self):
        self.interpreter = PFTInterpreter()
        self.report_template = self._load_report_template()
    
    def _load_report_template(self) -> Dict:
        return {
            'header': {
                'title': 'PULMONARY FUNCTION TEST REPORT',
                'subtitle': 'Automated Preliminary Interpretation',
                'disclaimer': 'This is a computer-generated preliminary report. Final interpretation should be confirmed by a qualified physician.'
            },
            'sections': [
                'demographics',
                'test_data',
                'interpretation',
                'clinical_impression',
                'recommendations',
                'technical_quality',
                'reference_standards'
            ]
        }
    
    def generate_comprehensive_report(self, pft_data: Dict, include_raw_data: bool = True) -> Dict:
        interpretation = self.interpreter.interpret_pft(pft_data)
        
        report = {
            'report_metadata': self._generate_report_metadata(),
            'patient_demographics': self._format_demographics(pft_data['demographics']),
            'test_results': self._format_test_results(pft_data['pft_results']),
            'predicted_values': self._calculate_and_format_predicted_values(pft_data),
            'interpretation_summary': self._format_interpretation_summary(interpretation),
            'detailed_analysis': self._format_detailed_analysis(interpretation, pft_data),
            'clinical_impression': self._format_clinical_impression(interpretation),
            'recommendations': self._format_recommendations(interpretation),
            'quality_indicators': self._assess_test_quality(pft_data),
            'reference_information': self._format_reference_info()
        }
        
        if include_raw_data:
            report['raw_interpretation_data'] = asdict(interpretation)
        
        return report
    
    def _generate_report_metadata(self) -> Dict:
        return {
            'report_generated': datetime.now().isoformat(),
            'generator_version': '1.0.0',
            'reference_equations': 'GLI-2012',
            'interpretation_guidelines': 'ATS/ERS 2022',
            'report_type': 'Automated Preliminary Interpretation',
            'requires_physician_review': True
        }
    
    def _format_demographics(self, demographics: Dict) -> Dict:
        bmi = demographics['weight_kg'] / ((demographics['height_cm'] / 100) ** 2)
        
        return {
            'age': f"{demographics['age']} years",
            'sex': 'Male' if demographics['sex'].upper() == 'M' else 'Female',
            'height': f"{demographics['height_cm']} cm ({demographics['height_cm'] / 2.54:.1f} inches)",
            'weight': f"{demographics['weight_kg']} kg ({demographics['weight_kg'] * 2.20462:.1f} lbs)",
            'bmi': f"{bmi:.1f} kg/m²",
            'bmi_category': self._classify_bmi(bmi)
        }
    
    def _classify_bmi(self, bmi: float) -> str:
        if bmi < 18.5:
            return 'Underweight'
        elif bmi < 25:
            return 'Normal weight'
        elif bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
    
    def _format_test_results(self, pft_results: Dict) -> Dict:
        pre = pft_results['pre_bronchodilator']
        post = pft_results['post_bronchodilator']
        
        fev1_change = post['fev1']['liters'] - pre['fev1']['liters']
        fvc_change = post['fvc']['liters'] - pre['fvc']['liters']
        fev1_percent_change = (fev1_change / pre['fev1']['liters']) * 100
        
        return {
            'pre_bronchodilator': {
                'fvc': {
                    'measured': f"{pre['fvc']['liters']:.2f} L",
                    'percent_predicted': f"{pre['fvc']['percent_predicted']}%",
                    'interpretation': self._interpret_percent_predicted(pre['fvc']['percent_predicted'])
                },
                'fev1': {
                    'measured': f"{pre['fev1']['liters']:.2f} L",
                    'percent_predicted': f"{pre['fev1']['percent_predicted']}%",
                    'interpretation': self._interpret_percent_predicted(pre['fev1']['percent_predicted'])
                },
                'fev1_fvc_ratio': {
                    'measured': f"{pre['fev1_fvc_ratio']['value']:.0f}%",
                    'interpretation': self._interpret_fev1_fvc_ratio(pre['fev1_fvc_ratio']['value'])
                }
            },
            'post_bronchodilator': {
                'fvc': {
                    'measured': f"{post['fvc']['liters']:.2f} L",
                    'percent_predicted': f"{post['fvc']['percent_predicted']}%",
                    'change': f"{fvc_change:+.2f} L"
                },
                'fev1': {
                    'measured': f"{post['fev1']['liters']:.2f} L",
                    'percent_predicted': f"{post['fev1']['percent_predicted']}%",
                    'change': f"{fev1_change:+.2f} L ({fev1_percent_change:+.1f}%)"
                },
                'fev1_fvc_ratio': {
                    'measured': f"{post['fev1_fvc_ratio']['value']:.0f}%",
                    'change': f"{post['fev1_fvc_ratio']['value'] - pre['fev1_fvc_ratio']['value']:+.0f}%"
                }
            },
            'bronchodilator_response': {
                'fev1_change_ml': f"{fev1_change * 1000:.0f} mL",
                'fev1_percent_change': f"{fev1_percent_change:.1f}%",
                'clinically_significant': fev1_percent_change > 12 and fev1_change > 0.2,
                'interpretation': self._interpret_bd_response(fev1_percent_change, fev1_change)
            }
        }
    
    def _interpret_percent_predicted(self, percent: int) -> str:
        if percent >= 80:
            return 'Normal'
        elif percent >= 70:
            return 'Mildly reduced'
        elif percent >= 60:
            return 'Moderately reduced'
        elif percent >= 50:
            return 'Moderately severely reduced'
        else:
            return 'Severely reduced'
    
    def _interpret_fev1_fvc_ratio(self, ratio: float) -> str:
        if ratio >= 70:
            return 'Normal'
        elif ratio >= 60:
            return 'Mildly reduced'
        elif ratio >= 50:
            return 'Moderately reduced'
        else:
            return 'Severely reduced'
    
    def _interpret_bd_response(self, percent_change: float, absolute_change: float) -> str:
        if percent_change >= 12 and absolute_change >= 0.2:
            return 'Significant positive response'
        elif percent_change >= 8:
            return 'Borderline positive response'
        else:
            return 'No significant response'
    
    def _calculate_and_format_predicted_values(self, pft_data: Dict) -> Dict:
        demographics = pft_data['demographics']
        predicted = self.interpreter.calculate_predicted_values(
            demographics['age'],
            demographics['height_cm'],
            demographics['sex']
        )
        
        return {
            'reference_equation': 'Global Lung Initiative (GLI) 2012',
            'ethnicity': 'Caucasian (default)',
            'predicted_values': {
                'fev1': f"{predicted['fev1_predicted']:.2f} L",
                'fvc': f"{predicted['fvc_predicted']:.2f} L",
                'fev1_fvc_ratio': f"{predicted['fev1_fvc_predicted'] * 100:.1f}%"
            },
            'lower_limit_normal': {
                'note': 'LLN calculated at 5th percentile (Z-score = -1.645)'
            }
        }
    
    def _format_interpretation_summary(self, interpretation: PFTInterpretation) -> Dict:
        return {
            'ventilatory_pattern': interpretation.pattern.value,
            'overall_severity': interpretation.severity.value,
            'bronchodilator_response': 'Positive' if interpretation.bronchodilator_response else 'Negative',
            'reversibility': 'Reversible' if interpretation.reversible else 'Fixed',
            'primary_finding': self._generate_primary_finding(interpretation),
            'confidence_indicator': f"{interpretation.confidence_score}%"
        }
    
    def _generate_primary_finding(self, interpretation: PFTInterpretation) -> str:
        if interpretation.pattern == Pattern.NORMAL:
            return "Normal spirometry"
        elif interpretation.pattern == Pattern.OBSTRUCTIVE:
            reversibility = "reversible" if interpretation.reversible else "fixed"
            return f"{interpretation.severity.value} {reversibility} obstructive pattern"
        elif interpretation.pattern == Pattern.RESTRICTIVE:
            return f"{interpretation.severity.value} restrictive pattern"
        else:
            return f"{interpretation.severity.value} mixed ventilatory pattern"
    
    def _format_detailed_analysis(self, interpretation: PFTInterpretation, pft_data: Dict) -> Dict:
        return {
            'z_scores': {
                'fev1': f"{interpretation.z_scores['fev1_z']:.2f}",
                'fvc': f"{interpretation.z_scores['fvc_z']:.2f}",
                'fev1_fvc_ratio': f"{interpretation.z_scores['fev1_fvc_z']:.2f}",
                'interpretation_note': 'Z-scores represent number of standard deviations from predicted mean'
            },
            'percentiles': {
                'fev1': f"{interpretation.percentiles['fev1_percentile']:.1f}th percentile",
                'fvc': f"{interpretation.percentiles['fvc_percentile']:.1f}th percentile",
                'fev1_fvc_ratio': f"{interpretation.percentiles['fev1_fvc_percentile']:.1f}th percentile"
            },
            'clinical_thresholds': {
                'fev1_fvc_lln_threshold': 'Values below 5th percentile (Z-score < -1.645) considered abnormal',
                'bronchodilator_significance': '≥12% and ≥200mL improvement considered significant'
            }
        }
    
    def _format_clinical_impression(self, interpretation: PFTInterpretation) -> Dict:
        return {
            'primary_impression': interpretation.clinical_impression,
            'differential_diagnosis': self._generate_differential_diagnosis(interpretation),
            'clinical_correlation': self._generate_clinical_correlation(interpretation)
        }
    
    def _generate_differential_diagnosis(self, interpretation: PFTInterpretation) -> List[str]:
        if interpretation.pattern == Pattern.OBSTRUCTIVE:
            if interpretation.reversible:
                return [
                    'Asthma',
                    'Reversible COPD component',
                    'Allergic bronchopulmonary aspergillosis',
                    'Vocal cord dysfunction (if upper airway involvement)'
                ]
            else:
                return [
                    'Chronic obstructive pulmonary disease (COPD)',
                    'Emphysema',
                    'Chronic bronchitis',
                    'Bronchiectasis'
                ]
        elif interpretation.pattern == Pattern.RESTRICTIVE:
            return [
                'Interstitial lung disease',
                'Pulmonary fibrosis',
                'Chest wall restriction',
                'Neuromuscular disease',
                'Pleural disease'
            ]
        elif interpretation.pattern == Pattern.MIXED:
            return [
                'Combined pulmonary fibrosis and emphysema',
                'COPD with restrictive component',
                'Sarcoidosis with airway involvement',
                'Advanced interstitial lung disease with secondary obstruction'
            ]
        else:
            return ['No specific pathology suggested']
    
    def _generate_clinical_correlation(self, interpretation: PFTInterpretation) -> str:
        correlations = []
        
        if interpretation.pattern == Pattern.OBSTRUCTIVE:
            correlations.append("Correlate with smoking history, occupational exposures, and symptom chronicity.")
            if interpretation.reversible:
                correlations.append("Consider asthma triggers, allergic history, and response to bronchodilator therapy.")
        
        elif interpretation.pattern == Pattern.RESTRICTIVE:
            correlations.append("Recommend chest imaging and consider autoimmune workup if indicated.")
            correlations.append("Evaluate for dyspnea on exertion and exercise tolerance.")
        
        elif interpretation.pattern == Pattern.MIXED:
            correlations.append("Complex pattern requiring comprehensive pulmonary evaluation.")
            correlations.append("Consider high-resolution CT chest for detailed assessment.")
        
        if interpretation.severity in [Severity.MODERATELY_SEVERE, Severity.SEVERE]:
            correlations.append("Severity suggests significant functional impairment warranting specialist evaluation.")
        
        return " ".join(correlations) if correlations else "Correlate with clinical presentation and symptoms."
    
    def _format_recommendations(self, interpretation: PFTInterpretation) -> Dict:
        return {
            'immediate_actions': self._get_immediate_recommendations(interpretation),
            'follow_up': self._get_followup_recommendations(interpretation),
            'additional_testing': self._get_additional_testing_recommendations(interpretation),
            'specialist_referral': self._get_referral_recommendations(interpretation)
        }
    
    def _get_immediate_recommendations(self, interpretation: PFTInterpretation) -> List[str]:
        recommendations = []
        
        if interpretation.pattern == Pattern.NORMAL:
            recommendations.append("Continue current health maintenance")
            recommendations.append("Monitor for development of respiratory symptoms")
        
        elif interpretation.reversible:
            recommendations.append("Consider trial of bronchodilator therapy")
            recommendations.append("Evaluate for asthma management if not already established")
        
        elif interpretation.severity in [Severity.SEVERE, Severity.VERY_SEVERE]:
            recommendations.append("Urgent pulmonology consultation recommended")
            recommendations.append("Consider oxygen saturation monitoring")
        
        return recommendations
    
    def _get_followup_recommendations(self, interpretation: PFTInterpretation) -> List[str]:
        recommendations = []
        
        if interpretation.pattern != Pattern.NORMAL:
            if interpretation.reversible:
                recommendations.append("Repeat spirometry in 3-6 months to assess treatment response")
            else:
                recommendations.append("Annual spirometry to monitor disease progression")
        
        if interpretation.pattern == Pattern.OBSTRUCTIVE and not interpretation.reversible:
            recommendations.append("Smoking cessation counseling if applicable")
            recommendations.append("Pneumococcal and annual influenza vaccination")
        
        return recommendations
    
    def _get_additional_testing_recommendations(self, interpretation: PFTInterpretation) -> List[str]:
        recommendations = []
        
        if interpretation.pattern == Pattern.RESTRICTIVE:
            recommendations.append("Complete pulmonary function testing with lung volumes and DLCO")
            recommendations.append("Chest X-ray or CT if not recently performed")
        
        elif interpretation.pattern == Pattern.MIXED:
            recommendations.append("Complete PFTs including lung volumes, DLCO, and respiratory muscle strength")
            recommendations.append("High-resolution CT chest")
        
        elif interpretation.pattern == Pattern.OBSTRUCTIVE and interpretation.severity != Severity.MILD:
            recommendations.append("Consider arterial blood gas analysis")
            recommendations.append("Six-minute walk test for functional assessment")
        
        return recommendations
    
    def _get_referral_recommendations(self, interpretation: PFTInterpretation) -> Dict:
        referrals = {
            'pulmonology': False,
            'cardiology': False,
            'rheumatology': False,
            'urgency': 'routine'
        }
        
        if interpretation.severity in [Severity.MODERATELY_SEVERE, Severity.SEVERE, Severity.VERY_SEVERE]:
            referrals['pulmonology'] = True
            referrals['urgency'] = 'urgent' if interpretation.severity == Severity.VERY_SEVERE else 'semi-urgent'
        
        elif interpretation.pattern == Pattern.RESTRICTIVE:
            referrals['pulmonology'] = True
            if interpretation.severity != Severity.MILD:
                referrals['rheumatology'] = True
        
        elif interpretation.pattern == Pattern.MIXED:
            referrals['pulmonology'] = True
            referrals['urgency'] = 'semi-urgent'
        
        return referrals
    
    def _assess_test_quality(self, pft_data: Dict) -> Dict:
        pre = pft_data['pft_results']['pre_bronchodilator']
        post = pft_data['pft_results']['post_bronchodilator']
        
        quality_indicators = {
            'data_completeness': 'Complete' if all([
                pre.get('fev1'), pre.get('fvc'), pre.get('fev1_fvc_ratio'),
                post.get('fev1'), post.get('fvc'), post.get('fev1_fvc_ratio')
            ]) else 'Incomplete',
            'biological_plausibility': self._check_biological_plausibility(pft_data),
            'internal_consistency': self._check_internal_consistency(pft_data),
            'quality_grade': 'A'
        }
        
        return quality_indicators
    
    def _check_biological_plausibility(self, pft_data: Dict) -> str:
        demographics = pft_data['demographics']
        pre = pft_data['pft_results']['pre_bronchodilator']
        
        age = demographics['age']
        fev1 = pre['fev1']['liters']
        fvc = pre['fvc']['liters']
        
        if age < 3 or age > 100:
            return 'Questionable age'
        if fev1 > fvc:
            return 'FEV1 > FVC (physiologically impossible)'
        if fev1 < 0.5 or fvc < 0.5:
            return 'Extremely low values - verify'
        if fev1 > 6 or fvc > 8:
            return 'Extremely high values - verify'
        
        return 'Plausible'
    
    def _check_internal_consistency(self, pft_data: Dict) -> str:
        pre = pft_data['pft_results']['pre_bronchodilator']
        post = pft_data['pft_results']['post_bronchodilator']
        
        calculated_pre_ratio = (pre['fev1']['liters'] / pre['fvc']['liters']) * 100
        reported_pre_ratio = pre['fev1_fvc_ratio']['value']
        
        if abs(calculated_pre_ratio - reported_pre_ratio) > 2:
            return 'Ratio calculation inconsistent'
        
        fev1_change = post['fev1']['liters'] - pre['fev1']['liters']
        if fev1_change < -0.3:
            return 'Unexpected post-bronchodilator decrease'
        
        return 'Consistent'
    
    def _format_reference_info(self) -> Dict:
        return {
            'reference_equations': {
                'primary': 'Global Lung Initiative (GLI) 2012',
                'population': 'Multi-ethnic reference values, 3-95 years',
                'citation': 'Quanjer PH, et al. Eur Respir J. 2012;40(6):1324-43'
            },
            'interpretation_guidelines': {
                'primary': 'ATS/ERS Task Force on Standardisation of Lung Function Testing',
                'bronchodilator_response': 'ATS/ERS 2005 criteria: ≥12% and ≥200mL',
                'lower_limit_normal': '5th percentile (Z-score ≤ -1.645)'
            },
            'quality_assurance': {
                'standards': 'ATS/ERS 2019 Technical Standards',
                'equipment_calibration': 'Daily calibration recommended',
                'technician_training': 'Certified pulmonary function technologist preferred'
            }
        }
    
    def generate_summary_report(self, pft_data: Dict) -> str:
        interpretation = self.interpreter.interpret_pft(pft_data)
        demographics = pft_data['demographics']
        
        summary_lines = [
            f"PULMONARY FUNCTION TEST - AUTOMATED PRELIMINARY REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"PATIENT: {demographics['age']} year old {'Male' if demographics['sex'].upper() == 'M' else 'Female'}",
            f"HEIGHT: {demographics['height_cm']} cm | WEIGHT: {demographics['weight_kg']} kg",
            f"",
            f"RESULTS SUMMARY:",
            f"Ventilatory Pattern: {interpretation.pattern.value}",
            f"Severity: {interpretation.severity.value}",
            f"Bronchodilator Response: {'Positive' if interpretation.bronchodilator_response else 'Negative'}",
            f"",
            f"CLINICAL IMPRESSION:",
            f"{interpretation.clinical_impression}",
            f"",
            f"RECOMMENDATIONS:"
        ]
        
        for i, rec in enumerate(interpretation.recommendations[:5], 1):
            summary_lines.append(f"{i}. {rec}")
        
        summary_lines.extend([
            f"",
            f"NOTE: This is a computer-generated preliminary report.",
            f"Final interpretation requires physician review and clinical correlation."
        ])
        
        return "\n".join(summary_lines)
    
    def export_to_json(self, pft_data: Dict, filename: str = None) -> str:
        report = self.generate_comprehensive_report(pft_data)
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            return filename
        else:
            return json.dumps(report, indent=2, default=str)
    
    def export_to_text(self, pft_data: Dict, filename: str = None) -> str:
        report = self.generate_comprehensive_report(pft_data)
        
        text_lines = [
            "="*80,
            report['report_metadata']['title'],
            report['report_metadata']['subtitle'],
            "="*80,
            f"Generated: {report['report_metadata']['report_generated']}",
            f"Reference: {report['predicted_values']['reference_equation']}",
            "",
            "PATIENT DEMOGRAPHICS:",
            f"Age: {report['patient_demographics']['age']}",
            f"Sex: {report['patient_demographics']['sex']}",
            f"Height: {report['patient_demographics']['height']}",
            f"Weight: {report['patient_demographics']['weight']}",
            f"BMI: {report['patient_demographics']['bmi']} ({report['patient_demographics']['bmi_category']})",
            "",
            "TEST RESULTS:",
            "Pre-Bronchodilator:",
            f"  FVC: {report['test_results']['pre_bronchodilator']['fvc']['measured']} ({report['test_results']['pre_bronchodilator']['fvc']['percent_predicted']})",
            f"  FEV1: {report['test_results']['pre_bronchodilator']['fev1']['measured']} ({report['test_results']['pre_bronchodilator']['fev1']['percent_predicted']})",
            f"  FEV1/FVC: {report['test_results']['pre_bronchodilator']['fev1_fvc_ratio']['measured']}",
            "",
            "Post-Bronchodilator:",
            f"  FVC: {report['test_results']['post_bronchodilator']['fvc']['measured']} ({report['test_results']['post_bronchodilator']['fvc']['percent_predicted']})",
            f"  FEV1: {report['test_results']['post_bronchodilator']['fev1']['measured']} ({report['test_results']['post_bronchodilator']['fev1']['percent_predicted']})",
            f"  FEV1/FVC: {report['test_results']['post_bronchodilator']['fev1_fvc_ratio']['measured']}",
            "",
            "INTERPRETATION:",
            f"Pattern: {report['interpretation_summary']['ventilatory_pattern']}",
            f"Severity: {report['interpretation_summary']['overall_severity']}",
            f"Bronchodilator Response: {report['interpretation_summary']['bronchodilator_response']}",
            "",
            "CLINICAL IMPRESSION:",
            report['clinical_impression']['primary_impression'],
            "",
            "RECOMMENDATIONS:"
        ]
        
        all_recommendations = []
        for category, recs in report['recommendations'].items():
            if isinstance(recs, list):
                all_recommendations.extend(recs)
        
        for i, rec in enumerate(all_recommendations, 1):
            text_lines.append(f"{i}. {rec}")
        
        text_lines.extend([
            "",
            "="*80,
            "DISCLAIMER:",
            "This is an automated preliminary interpretation.",
            "Final clinical correlation and interpretation must be performed by a qualified physician.",
            "="*80
        ])
        
        text_report = "\n".join(text_lines)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(text_report)
            return filename
        else:
            return text_report