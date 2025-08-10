import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Union
import logging
from datetime import datetime

from modules.PFT_interpreter import PFTInterpreter, Pattern, Severity
from modules.PFT_report import PFTReportGenerator

class PFTSystem:
    
    def __init__(self, log_level: str = 'INFO'):
        self.setup_logging(log_level)
        self.interpreter = PFTInterpreter()
        self.report_generator = PFTReportGenerator()
        self.processed_count = 0
        self.error_count = 0
        
        self.logger.info("PFT Interpretation System initialized")
    
    def setup_logging(self, log_level: str):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'pft_system_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_pft_data(self, data: Dict) -> tuple[bool, List[str]]:
        errors = []
        
        required_keys = ['demographics', 'pft_results']
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return False, errors
        
        demo_required = ['age', 'sex', 'height_cm', 'weight_kg']
        for key in demo_required:
            if key not in data['demographics']:
                errors.append(f"Missing demographic data: {key}")
        
        age = data['demographics'].get('age', 0)
        if not (3 <= age <= 100):
            errors.append(f"Age {age} outside valid range (3-100)")
        
        height = data['demographics'].get('height_cm', 0)
        if not (100 <= height <= 220):
            errors.append(f"Height {height}cm outside valid range (100-220)")
        
        sex = data['demographics'].get('sex', '').upper()
        if sex not in ['M', 'F']:
            errors.append(f"Invalid sex value: {sex} (should be M or F)")
        
        pft_keys = ['pre_bronchodilator', 'post_bronchodilator']
        for key in pft_keys:
            if key not in data['pft_results']:
                errors.append(f"Missing PFT data: {key}")
            else:
                measurement_keys = ['fvc', 'fev1', 'fev1_fvc_ratio']
                for mkey in measurement_keys:
                    if mkey not in data['pft_results'][key]:
                        errors.append(f"Missing measurement in {key}: {mkey}")
        
        if 'pre_bronchodilator' in data['pft_results']:
            pre = data['pft_results']['pre_bronchodilator']
            
            if 'fev1' in pre and 'fvc' in pre:
                fev1 = pre['fev1'].get('liters', 0)
                fvc = pre['fvc'].get('liters', 0)
                
                if fev1 > fvc:
                    errors.append("FEV1 cannot be greater than FVC")
                
                if fev1 < 0.3 or fvc < 0.3:
                    errors.append("Extremely low lung function values - please verify")
                
                if fev1 > 8 or fvc > 10:
                    errors.append("Extremely high lung function values - please verify")
        
        return len(errors) == 0, errors
    
    def process_single_pft(self, pft_data: Dict, output_format: str = 'json') -> Dict:
        try:
            is_valid, validation_errors = self.validate_pft_data(pft_data)
            if not is_valid:
                raise ValueError(f"Invalid PFT data: {'; '.join(validation_errors)}")
            
            interpretation = self.interpreter.interpret_pft(pft_data)
            
            if output_format.lower() == 'json':
                report = self.report_generator.generate_comprehensive_report(pft_data)
            elif output_format.lower() == 'text':
                report = self.report_generator.generate_summary_report(pft_data)
            else:
                report = self.report_generator.generate_comprehensive_report(pft_data)
            
            self.processed_count += 1
            self.logger.info(f"Successfully processed PFT - Pattern: {interpretation.pattern.value}, Severity: {interpretation.severity.value}")
            
            return {
                'status': 'success',
                'report': report,
                'interpretation': {
                    'pattern': interpretation.pattern.value,
                    'severity': interpretation.severity.value,
                    'reversible': interpretation.reversible
                }
            }
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error processing PFT: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'report': None
            }
    
    def process_batch_pfts(self, input_file: str, output_dir: str = 'output', output_format: str = 'json') -> Dict:
        self.logger.info(f"Starting batch processing from {input_file}")
        
        try:
            with open(input_file, 'r') as f:
                if input_file.endswith('.jsonl'):
                    pft_data_list = [json.loads(line) for line in f if line.strip()]
                else:
                    data = json.load(f)
                    if isinstance(data, list):
                        pft_data_list = data
                    else:
                        pft_data_list = [data]
            
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            results = {
                'processed': 0,
                'errors': 0,
                'summary': {
                    'normal': 0,
                    'obstructive': 0,
                    'restrictive': 0,
                    'mixed': 0
                },
                'severity_distribution': {
                    'normal': 0,
                    'mild': 0,
                    'moderate': 0,
                    'moderately_severe': 0,
                    'severe': 0,
                    'very_severe': 0
                },
                'files_generated': []
            }
            
            for idx, pft_data in enumerate(pft_data_list):
                try:
                    result = self.process_single_pft(pft_data, output_format)
                    
                    if result['status'] == 'success':
                        results['processed'] += 1
                        
                        pattern = result['interpretation']['pattern'].lower().replace(' ', '_')
                        severity = result['interpretation']['severity'].lower().replace(' ', '_')
                        
                        if pattern in results['summary']:
                            results['summary'][pattern] += 1
                        if severity in results['severity_distribution']:
                            results['severity_distribution'][severity] += 1
                        
                        filename = f"pft_report_{idx+1:04d}"
                        if pft_data.get('file_name'):
                            filename = Path(pft_data['file_name']).stem
                        
                        if output_format.lower() == 'json':
                            output_file = output_path / f"{filename}_report.json"
                            with open(output_file, 'w') as f:
                                json.dump(result['report'], f, indent=2, default=str)
                        else:
                            output_file = output_path / f"{filename}_report.txt"
                            with open(output_file, 'w') as f:
                                f.write(result['report'])
                        
                        results['files_generated'].append(str(output_file))
                        
                    else:
                        results['errors'] += 1
                        self.logger.error(f"Failed to process PFT {idx+1}: {result['error']}")
                
                except Exception as e:
                    results['errors'] += 1
                    self.logger.error(f"Exception processing PFT {idx+1}: {str(e)}")
            
            summary_report = self.generate_batch_summary(results, pft_data_list)
            summary_file = output_path / "batch_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary_report, f, indent=2, default=str)
            
            results['files_generated'].append(str(summary_file))
            
            self.logger.info(f"Batch processing complete: {results['processed']} successful, {results['errors']} errors")
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_batch_summary(self, results: Dict, pft_data_list: List[Dict]) -> Dict:
        total = len(pft_data_list)
        
        summary = {
            'batch_metadata': {
                'total_pfts': total,
                'processed_successfully': results['processed'],
                'processing_errors': results['errors'],
                'success_rate': f"{(results['processed']/total)*100:.1f}%" if total > 0 else "0%",
                'processing_date': datetime.now().isoformat()
            },
            'pattern_distribution': results['summary'],
            'severity_distribution': results['severity_distribution'],
            'demographics_summary': self.analyze_demographics(pft_data_list),
            'clinical_insights': self.generate_clinical_insights(results, pft_data_list)
        }
        
        return summary
    
    def analyze_demographics(self, pft_data_list: List[Dict]) -> Dict:
        ages = []
        sexes = {'M': 0, 'F': 0}
        heights = []
        
        for pft in pft_data_list:
            if 'demographics' in pft:
                demo = pft['demographics']
                if 'age' in demo:
                    ages.append(demo['age'])
                if 'sex' in demo:
                    sex = demo['sex'].upper()
                    if sex in sexes:
                        sexes[sex] += 1
                if 'height_cm' in demo:
                    heights.append(demo['height_cm'])
        
        return {
            'age_statistics': {
                'mean': sum(ages) / len(ages) if ages else 0,
                'min': min(ages) if ages else 0,
                'max': max(ages) if ages else 0,
                'count': len(ages)
            },
            'sex_distribution': sexes,
            'height_statistics': {
                'mean': sum(heights) / len(heights) if heights else 0,
                'min': min(heights) if heights else 0,
                'max': max(heights) if heights else 0,
                'count': len(heights)
            }
        }
    
    def generate_clinical_insights(self, results: Dict, pft_data_list: List[Dict]) -> Dict:
        total_processed = results['processed']
        
        if total_processed == 0:
            return {'note': 'No successful interpretations to analyze'}
        
        insights = {
            'abnormal_rate': f"{((total_processed - results['summary']['normal']) / total_processed) * 100:.1f}%",
            'obstructive_predominance': results['summary']['obstructive'] > results['summary']['restrictive'],
            'severe_cases': results['severity_distribution']['severe'] + results['severity_distribution'].get('very_severe', 0),
            'reversibility_noted': 'Analysis would require individual case review',
            'quality_indicators': {
                'processing_success_rate': f"{(results['processed'] / len(pft_data_list)) * 100:.1f}%",
                'data_completeness': 'Assessed per individual case'
            }
        }
        
        return insights
    
    def run_quality_assessment(self, input_file: str) -> Dict:
        self.logger.info("Running quality assessment")
        
        try:
            with open(input_file, 'r') as f:
                if input_file.endswith('.jsonl'):
                    pft_data_list = [json.loads(line) for line in f if line.strip()]
                else:
                    data = json.load(f)
                    pft_data_list = data if isinstance(data, list) else [data]
            
            quality_results = {
                'total_records': len(pft_data_list),
                'valid_records': 0,
                'invalid_records': 0,
                'validation_errors': {},
                'data_quality_metrics': {
                    'complete_demographics': 0,
                    'complete_pft_data': 0,
                    'biological_plausibility_issues': 0
                }
            }
            
            for idx, pft_data in enumerate(pft_data_list):
                is_valid, errors = self.validate_pft_data(pft_data)
                
                if is_valid:
                    quality_results['valid_records'] += 1
                    quality_results['data_quality_metrics']['complete_demographics'] += 1
                    quality_results['data_quality_metrics']['complete_pft_data'] += 1
                else:
                    quality_results['invalid_records'] += 1
                    quality_results['validation_errors'][f'record_{idx+1}'] = errors
            
            return quality_results
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='Automated PFT Interpretation System')
    parser.add_argument('command', choices=['single', 'batch', 'quality'], 
                       help='Operation mode')
    parser.add_argument('--input', '-i', required=True, 
                       help='Input file (JSON for single/batch, JSON/JSONL for batch)')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate data without processing')
    
    args = parser.parse_args()
    
    pft_system = PFTSystem(log_level=args.log_level)
    
    try:
        if args.command == 'single':
            with open(args.input, 'r') as f:
                pft_data = json.load(f)
            
            if args.validate_only:
                is_valid, errors = pft_system.validate_pft_data(pft_data)
                if is_valid:
                    print("✓ PFT data is valid")
                    return 0
                else:
                    print("✗ PFT data validation failed:")
                    for error in errors:
                        print(f"  - {error}")
                    return 1
            
            result = pft_system.process_single_pft(pft_data, args.format)
            
            if result['status'] == 'success':
                output_path = Path(args.output)
                output_path.mkdir(exist_ok=True)
                
                if args.format == 'json':
                    output_file = output_path / 'pft_report.json'
                    with open(output_file, 'w') as f:
                        json.dump(result['report'], f, indent=2, default=str)
                else:
                    output_file = output_path / 'pft_report.txt'
                    with open(output_file, 'w') as f:
                        f.write(result['report'])
                
                print(f"✓ Report generated: {output_file}")
                print(f"Pattern: {result['interpretation']['pattern']}")
                print(f"Severity: {result['interpretation']['severity']}")
                return 0
            else:
                print(f"✗ Processing failed: {result['error']}")
                return 1
        
        elif args.command == 'batch':
            if args.validate_only:
                quality_results = pft_system.run_quality_assessment(args.input)
                print(f"Quality Assessment Results:")
                print(f"Total records: {quality_results['total_records']}")
                print(f"Valid records: {quality_results['valid_records']}")
                print(f"Invalid records: {quality_results['invalid_records']}")
                
                if quality_results['invalid_records'] > 0:
                    print("\nValidation errors found:")
                    for record, errors in quality_results['validation_errors'].items():
                        print(f"  {record}: {'; '.join(errors)}")
                    return 1
                return 0
            
            results = pft_system.process_batch_pfts(args.input, args.output, args.format)
            
            if 'error' not in results:
                print(f"✓ Batch processing complete")
                print(f"Processed: {results['processed']} PFTs")
                print(f"Errors: {results['errors']}")
                print(f"Files generated: {len(results['files_generated'])}")
                print(f"\nPattern distribution:")
                for pattern, count in results['summary'].items():
                    print(f"  {pattern.title()}: {count}")
                return 0
            else:
                print(f"✗ Batch processing failed: {results['error']}")
                return 1
        
        elif args.command == 'quality':
            quality_results = pft_system.run_quality_assessment(args.input)
            
            output_path = Path(args.output)
            output_path.mkdir(exist_ok=True)
            quality_file = output_path / 'quality_assessment.json'
            
            with open(quality_file, 'w') as f:
                json.dump(quality_results, f, indent=2, default=str)
            
            print(f"✓ Quality assessment complete: {quality_file}")
            print(f"Total records: {quality_results['total_records']}")
            print(f"Valid: {quality_results['valid_records']}")
            print(f"Invalid: {quality_results['invalid_records']}")
            
            if quality_results['invalid_records'] > 0:
                print(f"Success rate: {(quality_results['valid_records']/quality_results['total_records'])*100:.1f}%")
            
            return 0
    
    except FileNotFoundError:
        print(f"✗ Input file not found: {args.input}")
        return 1
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        pft_system.logger.error(f"Unexpected error: {e}")
        return 1

def create_sample_pft_data() -> Dict:
    return {
        "file_name": "sample_pft.pdf",
        "demographics": {
            "age": 65,
            "sex": "M",
            "height_cm": 175.0,
            "weight_kg": 88.0
        },
        "pft_results": {
            "pre_bronchodilator": {
                "fvc": {"liters": 3.95, "percent_predicted": 98},
                "fev1": {"liters": 2.53, "percent_predicted": 78},
                "fev1_fvc_ratio": {"value": 64}
            },
            "post_bronchodilator": {
                "fvc": {"liters": 4.15, "percent_predicted": 103},
                "fev1": {"liters": 2.91, "percent_predicted": 90},
                "fev1_fvc_ratio": {"value": 70}
            }
        },
        "bronchodilator_response": {"fev1_percent_change": 15}
    }

def demo_single_interpretation():
    print("=== PFT Interpretation System Demo ===\n")
    
    sample_data = create_sample_pft_data()
    
    pft_system = PFTSystem(log_level='INFO')
    
    result = pft_system.process_single_pft(sample_data, 'text')
    
    if result['status'] == 'success':
        print("SAMPLE PFT INTERPRETATION REPORT:")
        print("=" * 50)
        print(result['report'])
        print("=" * 50)
        print(f"\nInterpretation Summary:")
        print(f"Pattern: {result['interpretation']['pattern']}")
        print(f"Severity: {result['interpretation']['severity']}")
        print(f"Reversible: {result['interpretation']['reversible']}")
    else:
        print(f"Error: {result['error']}")

def create_batch_sample_data(num_samples: int = 5) -> List[Dict]:
    import random
    
    samples = []
    patterns = [
        {"fev1_pp": 95, "fvc_pp": 98, "ratio": 78, "bd_response": 5},
        {"fev1_pp": 82, "fvc_pp": 95, "ratio": 65, "bd_response": 8},
        {"fev1_pp": 65, "fvc_pp": 85, "ratio": 58, "bd_response": 18},
        {"fev1_pp": 68, "fvc_pp": 70, "ratio": 82, "bd_response": 3},
        {"fev1_pp": 55, "fvc_pp": 58, "ratio": 62, "bd_response": 12}
    ]
    
    for i in range(num_samples):
        pattern = patterns[i % len(patterns)]
        
        age = random.randint(25, 80)
        sex = random.choice(['M', 'F'])
        height = random.randint(150, 190) if sex == 'F' else random.randint(165, 200)
        weight = random.randint(50, 100)
        
        base_fev1 = 3.0 + (height - 170) * 0.02 + (25 - age) * 0.01
        base_fvc = 3.8 + (height - 170) * 0.025 + (25 - age) * 0.012
        
        pre_fev1 = base_fev1 * (pattern['fev1_pp'] / 100)
        pre_fvc = base_fvc * (pattern['fvc_pp'] / 100)
        pre_ratio = pattern['ratio']
        
        bd_change = pattern['bd_response'] / 100
        post_fev1 = pre_fev1 * (1 + bd_change)
        post_fvc = pre_fvc * (1 + bd_change * 0.3)
        post_ratio = (post_fev1 / post_fvc) * 100
        
        sample = {
            "file_name": f"batch_sample_{i+1}.pdf",
            "demographics": {
                "age": age,
                "sex": sex,
                "height_cm": height,
                "weight_kg": weight
            },
            "pft_results": {
                "pre_bronchodilator": {
                    "fvc": {"liters": round(pre_fvc, 2), "percent_predicted": pattern['fvc_pp']},
                    "fev1": {"liters": round(pre_fev1, 2), "percent_predicted": pattern['fev1_pp']},
                    "fev1_fvc_ratio": {"value": pre_ratio}
                },
                "post_bronchodilator": {
                    "fvc": {"liters": round(post_fvc, 2), "percent_predicted": int(pattern['fvc_pp'] * (1 + bd_change * 0.3))},
                    "fev1": {"liters": round(post_fev1, 2), "percent_predicted": int(pattern['fev1_pp'] * (1 + bd_change))},
                    "fev1_fvc_ratio": {"value": int(post_ratio)}
                }
            },
            "bronchodilator_response": {"fev1_percent_change": pattern['bd_response']}
        }
        
        samples.append(sample)
    
    return samples

def demo_batch_processing():
    print("=== Batch Processing Demo ===\n")
    
    batch_data = create_batch_sample_data(5)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(batch_data, f, indent=2)
        temp_file = f.name
    
    try:
        pft_system = PFTSystem(log_level='INFO')
        
        results = pft_system.process_batch_pfts(temp_file, 'demo_output', 'json')
        
        print("Batch Processing Results:")
        print(f"Processed: {results['processed']}")
        print(f"Errors: {results['errors']}")
        print("\nPattern Distribution:")
        for pattern, count in results['summary'].items():
            print(f"  {pattern.title()}: {count}")
        
        print(f"\nFiles generated in 'demo_output' directory:")
        for file_path in results['files_generated']:
            print(f"  - {Path(file_path).name}")
    
    finally:
        import os
        os.unlink(temp_file)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("PFT Interpretation System")
        print("=" * 30)
        print("Running in demo mode...\n")
        
        demo_single_interpretation()
        print("\n" + "="*80 + "\n")
        demo_batch_processing()
        
        print("\n" + "="*80)
        print("Demo complete! To use CLI mode, run with arguments:")
        print("python main_pft_system.py single --input sample.json")
        print("python main_pft_system.py batch --input batch_data.json --output results/")
        print("python main_pft_system.py quality --input data.json")
    else:
        sys.exit(main())